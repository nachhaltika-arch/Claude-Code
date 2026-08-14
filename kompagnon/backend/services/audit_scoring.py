"""
Bewertung: erhobene Fakten → Punkte je Kriterium.

Reine Funktionen ohne Netzwerkzugriff — dadurch vollständig testbar.
Jedes Ergebnis trägt seine Quelle (gemessen / abgeleitet / KI / nicht erhoben).
Wo nichts erhoben werden konnte, wird das Kriterium als 'nicht erhoben' markiert
und fällt aus der Score-Normierung heraus, statt als Null durchzuschlagen.
"""
from typing import Dict, List, Optional

from services.audit_criteria import (
    Source,
    ai_criteria,
    determine_level,
    find_criterion,
    ist_anwendbar,
    score_all,
)
from services.audit_industry_map import klasse_fuer_branche
from services.audit_industry_signals import zaehlt_in_klasse

Items = Dict[str, int]
Sources = Dict[str, Source]

# Die Fassung des Standards, gegen die bewertet wurde. Ohne Stempel lässt sich
# ein Altbestand später nicht einordnen — und die Frage, ob Bestandsaudits neu
# gerechnet werden, ist ausdrücklich offen.
STANDARD_VERSION = "2026.2"

MIN_CONTENT_WORDS = 300
LEAN_FORM_FIELDS = 5


class _Sheet:
    """Sammelt Punkte und Quellen während der Bewertung."""

    def __init__(self) -> None:
        self.items: Items = {}
        self.sources: Sources = {}

    def set(self, key: str, points, source: Source) -> None:
        criterion = find_criterion(key)
        maximum = criterion.max_points if criterion else 1
        try:
            value = int(round(float(points or 0)))
        except (TypeError, ValueError):
            value = 0
        self.items[key] = max(0, min(value, maximum)) if maximum else max(0, value)
        self.sources[key] = source

    def scale(self, key: str, ratio: Optional[float], source: Source) -> None:
        """Anteilswert (0..1) auf die Punktzahl des Kriteriums abbilden."""
        if ratio is None:
            self.skip(key)
            return
        criterion = find_criterion(key)
        self.set(key, round(ratio * (criterion.max_points if criterion else 1)), source)

    def skip(self, key: str) -> None:
        """Kriterium als nicht erhoben markieren — fällt aus der Normierung."""
        self.items[key] = 0
        self.sources[key] = Source.NOT_COLLECTED


def _ok(fact: Optional[dict]) -> bool:
    return bool(fact) and fact.get("collected") is True


def _tier(value: Optional[float], thresholds) -> Optional[int]:
    """Erste passende Schwelle (Grenzwert, Punkte) — absteigend geprüft."""
    if value is None:
        return None
    for limit, points in thresholds:
        if value < limit:
            return points
    return 0


# ═══════════════════════════════════════════════════════════════════
# Recht & Compliance
# ═══════════════════════════════════════════════════════════════════

def _score_legal(sheet: _Sheet, facts: dict) -> None:
    legal = facts.get("legal") or {}
    consent = facts.get("consent") or {}
    third = facts.get("third_parties") or {}
    forms = facts.get("forms") or {}

    if _ok(legal):
        for key, block in (("rc_impressum", "impressum"), ("rc_datenschutz", "datenschutz")):
            page = legal.get(block, {})
            points = 0
            if page.get("reachable"):
                points = 3 + (3 if page.get("complete") else 0)
            sheet.set(key, points, Source.MEASURED)
        sheet.set("rc_bfsg", 2 if legal.get("bfsg", {}).get("linked") else 0, Source.MEASURED)
    else:
        for key in ("rc_impressum", "rc_datenschutz", "rc_bfsg"):
            sheet.skip(key)

    if _ok(consent):
        if consent.get("cmp_detected"):
            sheet.set("rc_cookie", 4, Source.MEASURED)
        elif _ok(third) and third.get("count", 0) == 0:
            # Ohne einwilligungspflichtige Dienste ist kein Banner nötig.
            sheet.set("rc_cookie", 4, Source.DERIVED)
        else:
            sheet.set("rc_cookie", 0, Source.MEASURED)
    else:
        sheet.skip("rc_cookie")

    if _ok(forms) and forms.get("total", 0) > 0:
        sheet.set("rc_formular_dsgvo", 2 if forms.get("all_consent")
                  else (1 if forms.get("with_consent", 0) else 0), Source.MEASURED)
    else:
        sheet.skip("rc_formular_dsgvo")


# ═══════════════════════════════════════════════════════════════════
# Sicherheit & Datenschutz
# ═══════════════════════════════════════════════════════════════════

def _score_security(sheet: _Sheet, facts: dict) -> None:
    tls = facts.get("tls") or {}
    redirect = facts.get("redirect") or {}
    headers = facts.get("security_headers") or {}
    third = facts.get("third_parties") or {}
    consent = facts.get("consent") or {}

    if _ok(tls):
        if not tls.get("valid"):
            sheet.set("si_ssl", 0, Source.MEASURED)
        else:
            sheet.set("si_ssl", 2 if tls.get("expires_soon") else 3, Source.MEASURED)
    else:
        sheet.skip("si_ssl")

    if _ok(redirect):
        sheet.set("si_redirect", 2 if redirect.get("redirects") else 0, Source.MEASURED)
    else:
        sheet.skip("si_redirect")

    if _ok(headers):
        present = sum(1 for k in ("hsts", "csp", "xframe", "xcontent") if headers.get(k))
        sheet.scale("si_header", present / 4, Source.MEASURED)
    else:
        sheet.skip("si_header")

    if _ok(third):
        has_cmp = bool(consent.get("cmp_detected"))
        points = 2
        if third.get("external_fonts"):
            points -= 1
        if third.get("tracking_services") and not has_cmp:
            points -= 1
        sheet.set("si_drittanbieter", max(0, points), Source.MEASURED)
    else:
        sheet.skip("si_drittanbieter")


# ═══════════════════════════════════════════════════════════════════
# Performance & Core Web Vitals
# ═══════════════════════════════════════════════════════════════════

def _score_performance(sheet: _Sheet, facts: dict) -> None:
    psi = facts.get("psi_mobile") or {}
    images = facts.get("images") or {}

    if _ok(psi):
        _set_or_skip(sheet, "tp_lcp", _tier(psi.get("lcp_seconds"), ((2.5, 4), (4.0, 2))))
        _set_or_skip(sheet, "tp_cls", _tier(psi.get("cls_value"), ((0.1, 3), (0.25, 1))))
        # INP stammt nur aus CrUX-Felddaten; für kleine Betriebsseiten meist leer.
        _set_or_skip(sheet, "tp_inp", _tier(psi.get("inp_ms"), ((200, 2), (500, 1))))

        perf = psi.get("performance_score")
        if perf is None:
            sheet.skip("tp_mobile")
        else:
            sheet.set("tp_mobile", 3 if perf >= 90 else (2 if perf >= 70 else
                      (1 if perf >= 50 else 0)), Source.MEASURED)
    else:
        for key in ("tp_lcp", "tp_cls", "tp_inp", "tp_mobile"):
            sheet.skip(key)

    if _ok(images) and images.get("total", 0) > 0:
        points = sum([
            1 if images.get("modern_share", 0) >= 50 else 0,
            1 if images.get("lazy_share", 0) >= 50 else 0,
            1 if images.get("dimension_share", 0) >= 80 and images.get("oversized", 1) == 0 else 0,
        ])
        sheet.set("tp_bilder", points, Source.MEASURED)
    else:
        sheet.skip("tp_bilder")


def _set_or_skip(sheet: _Sheet, key: str, points: Optional[int]) -> None:
    if points is None:
        sheet.skip(key)
    else:
        sheet.set(key, points, Source.MEASURED)


# ═══════════════════════════════════════════════════════════════════
# Barrierefreiheit
# ═══════════════════════════════════════════════════════════════════

def _score_accessibility(sheet: _Sheet, facts: dict) -> None:
    psi = facts.get("psi_mobile") or {}
    qa = facts.get("qa") or {}
    audits = (psi.get("a11y_audits") or {}) if _ok(psi) else {}

    score = psi.get("accessibility_score") if _ok(psi) else None
    if score is None:
        sheet.skip("bf_lighthouse")
    else:
        sheet.set("bf_lighthouse", 3 if score >= 90 else (2 if score >= 75 else
                  (1 if score >= 50 else 0)), Source.MEASURED)

    sheet.scale("bf_kontrast", audits.get("kontrast"), Source.MEASURED)
    sheet.scale("bf_tastatur", audits.get("tastatur"), Source.DERIVED)

    quote = qa.get("alt_texte_quote")
    if quote is None:
        sheet.skip("bf_alt")
    else:
        sheet.set("bf_alt", 2 if quote >= 95 else (1 if quote >= 80 else 0), Source.MEASURED)

    # Bewusst rein DOM-basiert: gemischt aus DOM und Lighthouse wäre das
    # Kriterium bei fehlendem PageSpeed nur halb prüfbar, würde aber voll
    # gewertet — genau der stille Abzug, den die Überarbeitung beseitigt.
    if not qa:
        sheet.skip("bf_semantik")
    else:
        sheet.set("bf_semantik", sum([
            1 if qa.get("h1_genau_eins") else 0,
            1 if qa.get("heading_struktur_ok") else 0,
        ]), Source.MEASURED)


# ═══════════════════════════════════════════════════════════════════
# SEO & Auffindbarkeit
# ═══════════════════════════════════════════════════════════════════

def _score_seo(sheet: _Sheet, facts: dict) -> None:
    qa = facts.get("qa") or {}
    if not qa:
        for key in ("se_meta", "se_struktur", "se_index", "se_schema", "se_lokal"):
            sheet.skip(key)
    else:
        city = (facts.get("city") or "").strip().lower()
        title = (qa.get("title_text") or "").lower()
        h1 = (qa.get("h1_text") or "").lower()

        sheet.set("se_meta", sum([
            1 if qa.get("title_vorhanden") and qa.get("title_laenge_ok") else 0,
            1 if qa.get("meta_desc_vorhanden") and qa.get("meta_desc_laenge_ok") else 0,
            1 if city and city in title else 0,
        ]), Source.MEASURED)

        words = facts.get("word_count") or 0
        sheet.set("se_struktur", sum([
            1 if qa.get("h1_genau_eins") and qa.get("h2_vorhanden") else 0,
            1 if words >= MIN_CONTENT_WORDS else 0,
        ]), Source.MEASURED)

        sheet.set("se_index", sum([
            1 if qa.get("robots_txt") and qa.get("robots_txt_indexiert") else 0,
            1 if qa.get("sitemap_xml") else 0,
            1 if qa.get("canonical_vorhanden") else 0,
        ]), Source.MEASURED)

        sheet.set("se_schema", sum([
            1 if qa.get("schema_markup") else 0,
            1 if qa.get("schema_localbusiness") else 0,
            1 if qa.get("schema_faq") else 0,
        ]), Source.MEASURED)

        contact = facts.get("contact") or {}
        sheet.set("se_lokal", sum([
            1 if city and (city in title or city in h1) else 0,
            1 if contact.get("tel_link") else 0,
            1 if qa.get("google_maps") or qa.get("schema_localbusiness") else 0,
        ]), Source.MEASURED)

    links = facts.get("links") or {}
    if links and "broken_links" in links:
        sheet.set("se_links", 1 if not links.get("broken_links") else 0, Source.MEASURED)
    else:
        sheet.skip("se_links")


# ═══════════════════════════════════════════════════════════════════
# Design & Gestaltung
# ═══════════════════════════════════════════════════════════════════

def _score_design(sheet: _Sheet, facts: dict) -> None:
    qa = facts.get("qa") or {}
    if qa:
        sheet.set("dg_mobil", 1 if qa.get("mobile_viewport") else 0, Source.MEASURED)
    else:
        sheet.skip("dg_mobil")
    # dg_aktualitaet, dg_typografie, dg_farbsystem, dg_bildqualitaet: KI (siehe _apply_ai)


# ═══════════════════════════════════════════════════════════════════
# Conversion & Nutzerführung
# ═══════════════════════════════════════════════════════════════════

def _treffer_in_klasse(eintraege, gruppe: str, klasse: str, ersatz: int) -> int:
    """Zählt die Einträge, deren Begriffe für diese Klasse einschlägig sind.

    `eintraege` ist ``None`` bei Fakten aus der Zeit vor dem Branchenmodell —
    dort bleibt der klassenunabhängige Wert, den die Erhebung mitgeliefert hat.
    Ein Altbestand soll sich durch diese Änderung nicht rückwirkend
    verschlechtern.
    """
    if eintraege is None:
        return ersatz
    return sum(1 for e in eintraege
               if zaehlt_in_klasse(e.get("begriffe"), gruppe, klasse))


def _score_conversion(sheet: _Sheet, facts: dict, klasse: str = "") -> None:
    cta = facts.get("cta") or {}
    contact = facts.get("contact") or {}
    trust = facts.get("trust") or {}

    if _ok(cta):
        count = _treffer_in_klasse(cta.get("elemente"), "cta", klasse,
                                   cta.get("cta_count", 0))
        sheet.set("cv_cta", 3 if count >= 3 else (2 if count >= 1 else 0), Source.DERIVED)
    else:
        sheet.skip("cv_cta")

    if _ok(contact):
        sheet.set("cv_kontakt", sum([
            1 if contact.get("tel_link") else 0,
            1 if contact.get("form_is_lean") else 0,
            1 if contact.get("response_time_stated") else 0,
        ]), Source.MEASURED)
    else:
        sheet.skip("cv_kontakt")

    if _ok(trust):
        signale = _vertrauenssignale(trust, klasse)
        sheet.set("cv_vertrauen", 3 if signale >= 4 else (2 if signale >= 2 else
                  (1 if signale >= 1 else 0)), Source.DERIVED)
    else:
        sheet.skip("cv_vertrauen")
    # cv_klarheit, cv_angebot: KI (siehe _apply_ai)


# ═══════════════════════════════════════════════════════════════════
# Inhalt & Substanz
# ═══════════════════════════════════════════════════════════════════

def _vertrauenssignale(trust: dict, klasse: str) -> int:
    """Wie viele Vertrauenssignale in dieser Klasse zählen.

    Vier der fünf Untergruppen sind branchenunabhängig. Nur der Nachweis der
    Befähigung heißt überall anders — der Meisterbrief des Handwerkers zählt
    beim Ingenieurbüro nicht und dessen Kammerzugehörigkeit nicht beim
    Handwerker. Vorher zählte für alle dieselbe handwerkliche Liste.
    """
    if "zertifikat_begriffe" not in trust:
        return trust.get("signal_count", 0)  # Fakten vor dem Branchenmodell

    generisch = sum(1 for gruppe in ("bewertungen", "referenzen", "team", "garantie")
                    if trust.get(gruppe))
    passend = zaehlt_in_klasse(trust.get("zertifikat_begriffe"), "zertifikate", klasse)
    return generisch + (1 if passend else 0)


def _score_content(sheet: _Sheet, facts: dict, klasse: str = "") -> None:
    services = facts.get("services") or {}
    freshness = facts.get("freshness") or {}

    if _ok(services):
        count = _treffer_in_klasse(services.get("seiten"), "leistungsseiten", klasse,
                                   services.get("service_page_count", 0))
        sheet.set("ih_leistungsseiten", 2 if count >= 3 else (1 if count >= 1 else 0),
                  Source.MEASURED)
    else:
        sheet.skip("ih_leistungsseiten")

    if _ok(freshness):
        current = freshness.get("copyright_current") or freshness.get("has_dated_content")
        sheet.set("ih_aktualitaet", 1 if current else 0, Source.MEASURED)
    else:
        sheet.skip("ih_aktualitaet")
    # ih_textqualitaet: KI (siehe _apply_ai)


# ═══════════════════════════════════════════════════════════════════
# KI-bewertete Kriterien
# ═══════════════════════════════════════════════════════════════════

def _apply_ai(sheet: _Sheet, ai: dict) -> None:
    """Trägt die KI-Bewertung ein — nur für Kriterien, die als KI markiert sind."""
    for criterion in ai_criteria():
        value = ai.get(criterion.key) if ai else None
        if value is None:
            sheet.skip(criterion.key)
        else:
            sheet.set(criterion.key, value, Source.AI)


# ═══════════════════════════════════════════════════════════════════
# Infrastruktur (ohne Punkte)
# ═══════════════════════════════════════════════════════════════════

def _score_infrastructure(sheet: _Sheet, facts: dict) -> None:
    hosting = facts.get("hosting") or {}
    cdn = facts.get("cdn") or {}

    sheet.set("ho_anbieter", 1 if hosting.get("hosting_provider") else 0, Source.MEASURED)
    sheet.set("ho_uptime", 1 if facts.get("reachable") else 0, Source.MEASURED)
    sheet.set("ho_cms", 1 if hosting.get("detected_technologies") else 0, Source.MEASURED)

    if _ok(cdn):
        sheet.set("ho_cdn", 1 if cdn.get("cdn_active") else 0, Source.MEASURED)
    else:
        sheet.skip("ho_cdn")


# ═══════════════════════════════════════════════════════════════════
# K.-o.-Kriterien
# ═══════════════════════════════════════════════════════════════════

def detect_blockers(facts: dict) -> List[str]:
    """Rechtliche Totalausfälle, die das Level unabhängig vom Score deckeln."""
    blockers: List[str] = []
    legal = facts.get("legal") or {}
    tls = facts.get("tls") or {}
    third = facts.get("third_parties") or {}
    consent = facts.get("consent") or {}

    if _ok(legal):
        if not legal.get("impressum", {}).get("reachable"):
            blockers.append("kein_impressum")
        if not legal.get("datenschutz", {}).get("reachable"):
            blockers.append("keine_datenschutzerklaerung")

    if _ok(tls) and not tls.get("valid"):
        blockers.append("kein_gueltiges_tls")

    if _ok(third) and third.get("tracking_services") and not consent.get("cmp_detected"):
        blockers.append("tracking_ohne_consent")

    return blockers


# ═══════════════════════════════════════════════════════════════════
# Einstiegspunkt
# ═══════════════════════════════════════════════════════════════════

def _klasse_aus_erkennung(ai: dict) -> tuple:
    """Die Branchenklasse und woher sie stammt.

    Bevorzugt wird, was `audit_ai` bereits zugeordnet hat. Ältere Ergebnisse
    tragen nur `branche` und `betriebsseite` — für die wird hier nachgeholt,
    damit ein Altbestand nicht plötzlich gegen den vollen Katalog läuft.
    Fehlt jede Erkennung, wird nichts unterstellt: Ein fehlgeschlagener
    KI-Aufruf darf keine Kriterien verschwinden lassen.
    """
    if not ai:
        return "", ""
    if ai.get("branchenklasse"):
        return ai["branchenklasse"], ai.get("branchenklasse_quelle") or "map"
    if "branche" in ai or "betriebsseite" in ai:
        zuordnung = klasse_fuer_branche(
            ai.get("branche"), bool(ai.get("betriebsseite", True)))
        return zuordnung.klasse, zuordnung.quelle
    return "", ""


def _verwerfe_nicht_anwendbare(sheet: _Sheet, klasse: str) -> None:
    """Was für diese Branchenklasse nicht gilt, zählt nicht mit.

    Der Unterschied zu 'nicht erhoben' ist keine Feinheit: Das eine heißt, dass
    unsere Prüfung ausfiel, das andere, dass der Maßstab nicht passt. Nur das
    zweite darf man dem Betrieb erklären, ohne ihn zu beschämen.
    """
    if not klasse:
        return
    for key in list(sheet.sources):
        if not ist_anwendbar(key, klasse):
            sheet.items[key] = 0
            sheet.sources[key] = Source.NOT_APPLICABLE


def score_audit(facts: dict, ai: Optional[dict] = None) -> dict:
    """Bewertet alle Kriterien und liefert Punkte, Quellen, Score und Level."""
    sheet = _Sheet()
    ai = ai or {}

    # Die Klasse steht vor der Bewertung fest, nicht danach: Zwei Kriterien
    # zählen nur, was zur Branche passt (Leistungsseiten, Vertrauenssignale,
    # Zielhandlung). Die Erhebung konnte das noch nicht wissen — sie lief, bevor
    # das Modell die Seite gesehen hatte.
    klasse, quelle = _klasse_aus_erkennung(ai)

    _score_legal(sheet, facts)
    _score_security(sheet, facts)
    _score_performance(sheet, facts)
    _score_accessibility(sheet, facts)
    _score_seo(sheet, facts)
    _score_design(sheet, facts)
    _score_conversion(sheet, facts, klasse)
    _score_content(sheet, facts, klasse)
    _apply_ai(sheet, ai)
    _score_infrastructure(sheet, facts)

    _verwerfe_nicht_anwendbare(sheet, klasse)

    summary = score_all(sheet.items, sheet.sources, klasse)
    blockers = detect_blockers(facts)
    level = determine_level(summary["total_score"], blockers)

    return {
        **summary,
        "standard_version": STANDARD_VERSION,
        "branche": ai.get("branche", ""),
        "betriebsseite": ai.get("betriebsseite"),
        "branchenklasse": klasse,
        "branchenklasse_quelle": quelle,
        # Der Name aus dem Ausgabeformat der Bewertungslogik (§ 7). Dieselbe
        # Zahl wie `achieved_points`; beide stehen da, weil das Dokument den
        # einen und der Bestandscode den anderen Namen benutzt.
        "rohpunkte": summary["achieved_points"],
        "anwendbares_maximum": summary["applicable_max"],
        "items": sheet.items,
        "sources": {k: v.value for k, v in sheet.sources.items()},
        "blockers": blockers,
        "level": level,
    }
