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
from services import a11y_browser
from services.audit_industry_map import klasse_fuer_branche
from services.audit_industry_signals import (
    ORT_IM_TITEL_ERWARTET,
    kontakt_merkmale,
    schema_passt,
    treffer as signal_treffer,
    zaehlt_in_klasse,
)

Items = Dict[str, int]
Sources = Dict[str, Source]

# Die Fassung des Standards, gegen die bewertet wurde. Ohne Stempel lässt sich
# ein Altbestand später nicht einordnen — und die Frage, ob Bestandsaudits neu
# gerechnet werden, ist ausdrücklich offen.
STANDARD_VERSION = "2026.2"

MIN_CONTENT_WORDS = 300
LEAN_FORM_FIELDS = 5


def zahl(wert) -> str:
    """Eine Messzahl, wie sie im Bericht steht — deutsches Komma, keine Nullen.

    `3.4` wird zu „3,4", `90.0` zu „90". Der Beleg soll gelesen werden, nicht
    entziffert.
    """
    if isinstance(wert, bool):
        return "ja" if wert else "nein"
    if isinstance(wert, float):
        gerundet = round(wert, 2)
        text = f"{gerundet:.2f}".rstrip("0").rstrip(".")
        return text.replace(".", ",")
    return str(wert)


def teile_beleg(paare) -> str:
    """Beleg fuer ein Kriterium aus mehreren Teilpruefungen.

    `paare` ist eine Folge aus (erfuellt, Bezeichnung). Genannt werden **beide**
    Seiten: Was zaehlt und was fehlt. Ein Beleg, der nur die Maengel auffuehrt,
    liest sich als Anklage; einer, der nur die Erfolge nennt, erklaert den
    Abzug nicht.
    """
    ja = [name for erfuellt, name in paare if erfuellt]
    nein = [name for erfuellt, name in paare if not erfuellt]
    stuecke = []
    if ja:
        stuecke.append("erfüllt: " + ", ".join(ja))
    if nein:
        stuecke.append("offen: " + ", ".join(nein))
    return " · ".join(stuecke)


class _Sheet:
    """Sammelt Punkte, Quellen und Belege während der Bewertung.

    **Der Beleg ist seit dem 04.09.2026 dabei (L-151).** Der Bericht nannte je
    Kriterium den Katalog-Hinweis — *was* geprueft wird — und die Punktzahl,
    aber nicht den **gemessenen Wert**. Ein Fremdleser hat das als durchgehende
    Kritik zurueckgemeldet: „haeufig bleibt unklar, welcher konkrete Messwert
    zu dem Punktabzug gefuehrt hat."

    Der Beleg entsteht **an der Rechenstelle**, nicht in einem zweiten Modul
    daneben. Ein Beleg, der die Fakten ein zweites Mal liest, kann von der
    Punktzahl abweichen — und ein Beleg, der etwas anderes sagt als die Zahl,
    ist schlimmer als keiner.
    """

    def __init__(self) -> None:
        self.items: Items = {}
        self.sources: Sources = {}
        self.belege: Dict[str, str] = {}

    def set(self, key: str, points, source: Source, beleg: str = "") -> None:
        criterion = find_criterion(key)
        maximum = criterion.max_points if criterion else 1
        try:
            value = int(round(float(points or 0)))
        except (TypeError, ValueError):
            value = 0
        self.items[key] = max(0, min(value, maximum)) if maximum else max(0, value)
        self.sources[key] = source
        if beleg:
            self.belege[key] = beleg
        else:
            self.belege.pop(key, None)

    def scale(self, key: str, ratio: Optional[float], source: Source,
              beleg: str = "") -> None:
        """Anteilswert (0..1) auf die Punktzahl des Kriteriums abbilden."""
        if ratio is None:
            self.skip(key)
            return
        criterion = find_criterion(key)
        self.set(key, round(ratio * (criterion.max_points if criterion else 1)),
                 source, beleg)

    def skip(self, key: str) -> None:
        """Kriterium als nicht erhoben markieren — fällt aus der Normierung."""
        self.items[key] = 0
        self.sources[key] = Source.NOT_COLLECTED
        self.belege.pop(key, None)


def _ok(fact: Optional[dict]) -> bool:
    return bool(fact) and fact.get("collected") is True


def _nach_abstufung(sheet: _Sheet, key: str, wert, quelle: Source = Source.MEASURED,
                    einheit: str = "", zusatz: str = "") -> None:
    """Punkte nach der am Kriterium hinterlegten Abstufung vergeben.

    Bis zum 25.08.2026 standen die Schwellen hier — teils als Liste (`_tier`),
    teils als Bedingung mitten im Satz (`3 if perf >= 90 else ...`). Die zweite
    Form kann kein Ausleseprogramm lesen; das Buch musste seine Punktetabellen
    deshalb raten. Jetzt stehen die Zahlen in `audit_criteria.py`, wo auch die
    Punktwerte stehen, und diese Funktion holt sie sich von dort.

    Der Fall `wert is None` heißt: nicht erhoben. Er wird übersprungen, nicht
    mit null Punkten bewertet — sonst verkauft die Auswertung eine fehlende
    Messung als Mangel.
    """
    if wert is None:
        sheet.skip(key)
        return
    criterion = find_criterion(key)
    if criterion is None or criterion.abstufung is None:
        raise ValueError(f"Kriterium ohne hinterlegte Abstufung: {key}")
    stufe = criterion.abstufung.stufe_fuer(wert)
    beleg = f"Gemessen: {zahl(wert)}{einheit} — {stufe.bedingung}" if stufe.bedingung \
        else f"Gemessen: {zahl(wert)}{einheit}"
    if zusatz:
        beleg += f" · {zusatz}"
    sheet.set(key, stufe.punkte, quelle, beleg)


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
            sheet.set(key, points, Source.MEASURED, teile_beleg((
                (page.get("reachable"), "Seite erreichbar"),
                (page.get("complete"), "Pflichtangaben vollständig"),
            )))
            verlinkt = bool(legal.get("bfsg", {}).get("linked"))
        sheet.set("rc_bfsg", 2 if verlinkt else 0, Source.MEASURED,
                  "Erklärung zur Barrierefreiheit verlinkt" if verlinkt
                  else "Keine Erklärung zur Barrierefreiheit gefunden")
    else:
        for key in ("rc_impressum", "rc_datenschutz", "rc_bfsg"):
            sheet.skip(key)

    if _ok(consent):
        dienste = ", ".join(third.get("services") or []) if _ok(third) else ""
        if consent.get("cmp_detected"):
            sheet.set("rc_cookie", 4, Source.MEASURED,
                      "Consent-Tool erkannt: " + ", ".join(consent.get("cmp_names") or []))
        elif _ok(third) and third.get("count", 0) == 0:
            # Ohne einwilligungspflichtige Dienste ist kein Banner nötig.
            sheet.set("rc_cookie", 4, Source.DERIVED,
                      "Kein einwilligungspflichtiger Dienst gefunden — kein Banner nötig")
        else:
            # **Der Beleg nennt den Ausloeser (L-151).** Bis zum 04.09.2026 stand
            # hier nur „0 von 4". Ein Fremdleser hat daraus geschlossen, die
            # Pruefung sei kaputt — sie hatte nur nie gesagt, welcher Dienst sie
            # ausloest.
            sheet.set("rc_cookie", 0, Source.MEASURED,
                      (f"Gefunden: {dienste} · kein Consent-Tool erkannt" if dienste
                       else "Kein Consent-Tool erkannt"))
    else:
        sheet.skip("rc_cookie")

    if _ok(forms) and forms.get("total", 0) > 0:
        mit = forms.get("with_consent", 0)
        gesamt = forms.get("total", 0)
        sheet.set("rc_formular_dsgvo", 2 if forms.get("all_consent")
                  else (1 if mit else 0), Source.MEASURED,
                  f"{mit} von {gesamt} Formularen mit Einwilligungsfeld")
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
            sheet.set("si_ssl", 0, Source.MEASURED, "Zertifikat ungültig oder Handshake gescheitert")
        else:
            bald = tls.get("expires_soon")
            sheet.set("si_ssl", 2 if bald else 3, Source.MEASURED,
                      "Zertifikat gültig, läuft aber bald ab" if bald
                      else "Zertifikat gültig")
    else:
        sheet.skip("si_ssl")

    if _ok(redirect):
        leitet = bool(redirect.get("redirects"))
        sheet.set("si_redirect", 2 if leitet else 0, Source.MEASURED,
                  "http leitet auf https weiter" if leitet
                  else "Die http-Adresse leitet nicht auf https weiter")
    else:
        sheet.skip("si_redirect")

    if _ok(headers):
        namen = {"hsts": "HSTS", "csp": "CSP", "xframe": "X-Frame-Options",
                 "xcontent": "X-Content-Type-Options"}
        present = sum(1 for k in namen if headers.get(k))
        sheet.scale("si_header", present / 4, Source.MEASURED,
                    f"{present} von 4 Headern gesetzt · "
                    + teile_beleg([(headers.get(k), v) for k, v in namen.items()]))
    else:
        sheet.skip("si_header")

    if _ok(third):
        has_cmp = bool(consent.get("cmp_detected"))
        points = 2
        if third.get("external_fonts"):
            points -= 1
        if third.get("tracking_services") and not has_cmp:
            points -= 1
        sheet.set("si_drittanbieter", max(0, points), Source.MEASURED, teile_beleg((
            (not third.get("external_fonts"), "keine externen Schriften"),
            (not (third.get("tracking_services") and not has_cmp),
             "kein Tracking ohne Einwilligung"),
        )))
    else:
        sheet.skip("si_drittanbieter")


# ═══════════════════════════════════════════════════════════════════
# Performance & Core Web Vitals
# ═══════════════════════════════════════════════════════════════════

def _score_performance(sheet: _Sheet, facts: dict) -> None:
    psi = facts.get("psi_mobile") or {}
    images = facts.get("images") or {}

    if _ok(psi):
        _nach_abstufung(sheet, "tp_lcp", psi.get("lcp_seconds"), einheit=" s")
        _nach_abstufung(sheet, "tp_cls", psi.get("cls_value"))
        # INP stammt nur aus CrUX-Felddaten; für kleine Betriebsseiten meist leer.
        _nach_abstufung(sheet, "tp_inp", psi.get("inp_ms"), einheit=" ms")
        _nach_abstufung(sheet, "tp_mobile", psi.get("performance_score"), einheit=" von 100")
    else:
        for key in ("tp_lcp", "tp_cls", "tp_inp", "tp_mobile"):
            sheet.skip(key)

    if _ok(images) and images.get("total", 0) > 0:
        points = sum([
            1 if images.get("modern_share", 0) >= 50 else 0,
            1 if images.get("lazy_share", 0) >= 50 else 0,
            1 if images.get("dimension_share", 0) >= 80 and images.get("oversized", 1) == 0 else 0,
        ])
        sheet.set("tp_bilder", points, Source.MEASURED, teile_beleg((
            (images.get("modern_share", 0) >= 50,
             f"moderne Formate {zahl(images.get('modern_share', 0))} %"),
            (images.get("lazy_share", 0) >= 50,
             f"lazy geladen {zahl(images.get('lazy_share', 0))} %"),
            (images.get("dimension_share", 0) >= 80 and images.get("oversized", 1) == 0,
             f"Größenangaben {zahl(images.get('dimension_share', 0))} %"),
        )))
    else:
        sheet.skip("tp_bilder")


# ═══════════════════════════════════════════════════════════════════
# Barrierefreiheit
# ═══════════════════════════════════════════════════════════════════

def _score_accessibility(sheet: _Sheet, facts: dict) -> None:
    psi = facts.get("psi_mobile") or {}
    qa = facts.get("qa") or {}
    audits = (psi.get("a11y_audits") or {}) if _ok(psi) else {}

    _nach_abstufung(sheet, "bf_lighthouse",
                    psi.get("accessibility_score") if _ok(psi) else None)

    # **Lighthouse zuerst, der Browserlauf als Ersatz (L-153).** Faellt
    # PageSpeed aus, hing dieses Kriterium bisher mit ihm — und der Bericht
    # zeigte „Barrierefreiheit 0/2", weil von fuenf Kriterien eines uebrig
    # blieb. Die Reihenfolge ist Absicht: Waere die Eigenmessung erste Quelle,
    # verschoeben sich Punktzahlen im Bestand, ohne dass sich am Massstab
    # etwas geaendert haette.
    a11y = facts.get("a11y_browser") or {}
    if audits.get("kontrast") is not None:
        sheet.scale("bf_kontrast", audits.get("kontrast"), Source.MEASURED,
                    "Lighthouse-Prüfung der Farbkontraste bestanden"
                    if audits.get("kontrast") else
                    "Lighthouse meldet zu geringe Farbkontraste")
    else:
        anteil = a11y_browser.kontrast_anteil(a11y)
        verstoesse = a11y.get("kontrast_verstoesse") or 0
        geprueft = a11y.get("kontrast_geprueft") or 0
        beispiele = ", ".join(a11y.get("kontrast_beispiele") or [])
        beleg = (f"Am gerenderten Dokument gemessen: {verstoesse} von {geprueft} "
                 f"Textstellen unter dem geforderten Kontrast")
        if beispiele:
            beleg += f" — {beispiele}"
        if not verstoesse and geprueft:
            beleg = (f"Am gerenderten Dokument gemessen: alle {geprueft} "
                     f"Textstellen erreichen den geforderten Kontrast")
        sheet.scale("bf_kontrast", anteil, Source.MEASURED, beleg)
    if audits.get("tastatur") is not None:
        sheet.scale("bf_tastatur", audits.get("tastatur"), Source.DERIVED,
                    "Lighthouse findet keine Tastaturfalle"
                    if audits.get("tastatur") else
                    "Lighthouse meldet Mängel bei der Tastaturbedienung")
    else:
        # **Was hier nicht gemessen wird, sagt der Beleg.** Eine echte
        # Tastaturfalle findet man nur, indem man durchtabbt; geprueft sind
        # das Sprungziel und die erzwungene Reihenfolge.
        teile = teile_beleg((
            (a11y.get("skiplink"), "Sprungziel zum Inhalt"),
            (not a11y.get("positive_tabindex"), "keine erzwungene Tab-Reihenfolge"),
        ))
        sheet.scale("bf_tastatur", a11y_browser.tastatur_anteil(a11y), Source.DERIVED,
                    f"Am gerenderten Dokument geprüft — {teile}" if teile else "")

    # **Der Zusatz erklaert den Nenner (L-152).** Dekorative Bilder und
    # Zaehlpixel fallen aus der Zaehlung; ohne diesen Satz wundert sich ein
    # Betrieb, warum von zwoelf Bildern nur fuenf gewertet wurden.
    _inhalt = qa.get("bilder_inhalt")
    _ausgenommen = (qa.get("bilder_dekorativ") or 0) + (qa.get("bilder_pixel") or 0)
    _zusatz = ""
    if _inhalt is not None:
        _zusatz = f"{qa.get('bilder_mit_alt', 0)} von {_inhalt} Inhaltsbildern"
        if _ausgenommen:
            _zusatz += f", {_ausgenommen} dekorativ oder Zählpixel (nicht gewertet)"
    _nach_abstufung(sheet, "bf_alt", qa.get("alt_texte_quote"), einheit=" %",
                    zusatz=_zusatz)

    # ── bf_semantik: zwei Haelften zu je einem Punkt (S1.1, 24.08.2026) ──
    #
    # Der Kriterienhinweis verspricht vier Dinge: „genau eine H1, saubere
    # Hierarchie, lang-Attribut, Labels". Geprueft wurden bis zum 24.08.2026
    # nur die ersten beiden. `html-has-lang` und `label` lagen die ganze Zeit
    # in `A11Y_AUDIT_GROUPS` — berechnet und weggeworfen.
    #
    # **Warum die DOM-Haelfte jetzt einen Punkt statt zwei traegt.** Die
    # beiden alten Stufen ueberlappten sich: `heading_struktur_ok` verlangt
    # selbst schon `len(h1) == 1`. „Hierarchie ohne H1" gibt es nicht; die
    # zweite Stufe war nie unabhaengig. Ein Punkt fuer die Struktur, einer
    # fuer die Screenreader-Grundlagen — das ist dieselbe Hoechstpunktzahl bei
    # zwei tatsaechlich verschiedenen Fragen.
    #
    # **Warum ohne PageSpeed nicht gewertet wird.** Hier stand vorher „bewusst
    # rein DOM-basiert: gemischt waere das Kriterium bei fehlendem PageSpeed
    # nur halb pruefbar, wuerde aber voll gewertet — genau der stille Abzug,
    # den die Ueberarbeitung beseitigt." Der Einwand bleibt richtig; die
    # Antwort darauf ist nicht, die Haelfte wegzulassen, sondern das Kriterium
    # als **nicht erhoben** zu fuehren. Dann faellt es aus der Normierung,
    # statt einen Abzug zu erzeugen — so wie `bf_kontrast` und `bf_tastatur`
    # sich in derselben Lage verhalten.
    semantik = audits.get("semantik")
    if not qa or semantik is None:
        sheet.skip("bf_semantik")
    else:
        sheet.set("bf_semantik", sum([
            1 if qa.get("heading_struktur_ok") else 0,
            1 if semantik >= 1.0 else 0,
        ]), Source.MEASURED, teile_beleg((
            (qa.get("heading_struktur_ok"), "Überschriftenhierarchie sauber"),
            (semantik >= 1.0, "Lighthouse-Semantikprüfung bestanden"),
        )))


# ═══════════════════════════════════════════════════════════════════
# SEO & Auffindbarkeit
# ═══════════════════════════════════════════════════════════════════

def _titel_traegt_den_massstab(title: str, city: str, klasse: str) -> bool:
    """Der dritte Punkt bei Title & Meta — je Klasse ein anderer.

    Lokale Betriebe werden am Ort gemessen. Bei K4 und K5 sagt `PROFILE`
    ausdrücklich, dass ein Ort NICHT erwartet wird; dort trägt den Punkt, was
    stattdessen im Titel stehen soll — Leistung, Segment oder Sortiment. Vorher
    verlor ein bundesweiter Anbieter diesen Punkt zwangsläufig.
    """
    if not klasse or klasse in ORT_IM_TITEL_ERWARTET:
        return bool(city and city in title)
    return bool(signal_treffer(title, "leistungsseiten")
                and zaehlt_in_klasse(signal_treffer(title, "leistungsseiten"),
                                     "leistungsseiten", klasse))


def _score_seo(sheet: _Sheet, facts: dict, klasse: str = "") -> None:
    qa = facts.get("qa") or {}
    # Eine Seite, die erst im Browser entsteht, hat die Erhebung nie gesehen.
    # `se_struktur` und `se_lokal` haengen vollstaendig am ausgelieferten DOM;
    # sie mit 0 zu bewerten hiesse, dem Betrieb etwas zu bescheinigen, das
    # niemand geprueft hat. `se_meta` bleibt: Titel und Kurzbeschreibung
    # stehen in der Huelle und sind echt.
    nur_geruest = bool(facts.get("clientseitig"))
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
            1 if _titel_traegt_den_massstab(title, city, klasse) else 0,
        ]), Source.MEASURED, teile_beleg((
            (qa.get("title_vorhanden") and qa.get("title_laenge_ok"),
             "Seitentitel vorhanden und passend lang"),
            (qa.get("meta_desc_vorhanden") and qa.get("meta_desc_laenge_ok"),
             "Kurzbeschreibung vorhanden und passend lang"),
            (_titel_traegt_den_massstab(title, city, klasse),
             "Titel nennt Ort oder Leistung"),
        )))

        words = facts.get("word_count") or 0
        if nur_geruest:
            sheet.skip("se_struktur")
        else:
            sheet.set("se_struktur", sum([
                1 if qa.get("h1_genau_eins") and qa.get("h2_vorhanden") else 0,
                1 if words >= MIN_CONTENT_WORDS else 0,
            ]), Source.MEASURED, teile_beleg((
                (qa.get("h1_genau_eins") and qa.get("h2_vorhanden"),
                 "genau eine H1 mit H2-Gliederung"),
                (words >= MIN_CONTENT_WORDS,
                 f"Textumfang {words} Wörter (nötig: {MIN_CONTENT_WORDS})"),
            )))

        sheet.set("se_index", sum([
            1 if qa.get("robots_txt") and qa.get("robots_txt_indexiert") else 0,
            1 if qa.get("sitemap_xml") else 0,
            1 if qa.get("canonical_vorhanden") else 0,
        ]), Source.MEASURED, teile_beleg((
            (qa.get("robots_txt") and qa.get("robots_txt_indexiert"),
             "robots.txt vorhanden und ohne Aussperrung"),
            (qa.get("sitemap_xml"), "sitemap.xml"),
            (qa.get("canonical_vorhanden"), "Canonical-Angabe"),
        )))

        # Ohne `schema_typen` stammt die Erhebung von vor dem Branchenmodell —
        # dann bleibt es bei LocalBusiness und FAQ, damit ein Altbestand nicht
        # rückwirkend fällt.
        typen = qa.get("schema_typen")
        if typen is None:
            haupttyp = bool(qa.get("schema_localbusiness"))
            zusatz = bool(qa.get("schema_faq"))
        else:
            haupttyp = schema_passt(typen, klasse)
            zusatz = schema_passt(typen, klasse, zusatz=True)

        sheet.set("se_schema", sum([
            1 if qa.get("schema_markup") else 0,
            1 if haupttyp else 0,
            1 if zusatz else 0,
        ]), Source.MEASURED, teile_beleg((
            (qa.get("schema_markup"), "JSON-LD vorhanden"),
            (haupttyp, "passender Haupttyp"),
            (zusatz, "passender Zusatztyp"),
        )))

        contact = facts.get("contact") or {}
        if nur_geruest:
            sheet.skip("se_lokal")
        else:
            sheet.set("se_lokal", sum([
                1 if city and (city in title or city in h1) else 0,
                1 if contact.get("tel_link") else 0,
                1 if qa.get("google_maps") or qa.get("schema_localbusiness") else 0,
            ]), Source.MEASURED, teile_beleg((
                (city and (city in title or city in h1), "Ort in Titel oder H1"),
                (contact.get("tel_link"), "Telefonnummer als Link"),
                (qa.get("google_maps") or qa.get("schema_localbusiness"),
                 "Karte oder LocalBusiness-Auszeichnung"),
            )))

    # KI-Lesbarkeit (L-58 a). Die Werte stehen in `qa`, nicht eine Ebene
    # hoeher: `summarise_facts` hebt sie zwar hoch, aber `routers/audit.py:180`
    # uebergibt an `score_audit` die Ausgabe von **`collect_facts`**. Ein
    # Kriterium, das oben nachsieht, waere still nie gelaufen — dieselbe
    # Familie wie L-55 (gebaut, nie angeschlossen). Beim ersten Entwurf genau
    # so passiert und erst am Referenztest aufgefallen.
    #
    # `None` heisst ausdruecklich **unbekannt** und ist nicht dasselbe wie
    # `False`; ein Audit von vor dem 16.08. kennt die Felder gar nicht und
    # darf nicht rueckwirkend Punkte verlieren.
    _llms = qa.get("llms_txt") if qa else None
    _gesperrt = qa.get("gesperrte_ki_crawler") if qa else None
    if _llms is None and _gesperrt is None:
        sheet.skip("se_ki_lesbar")
    else:
        # Wer GPTBot aussperrt, ist fuer ChatGPT nicht vorhanden — das wiegt
        # schwerer als eine fehlende `llms.txt`, die kaum eine Seite hat.
        sheet.set("se_ki_lesbar", sum([
            2 if not (_gesperrt or []) else 0,
            1 if _llms else 0,
        ]), Source.MEASURED, teile_beleg((
            (not (_gesperrt or []),
             "kein KI-Crawler ausgesperrt" if not (_gesperrt or [])
             else "ausgesperrt: " + ", ".join(_gesperrt)),
            (_llms, "llms.txt vorhanden"),
        )))

    links = facts.get("links") or {}
    if links and "broken_links" in links:
        kaputt = links.get("broken_links") or []
        sheet.set("se_links", 0 if kaputt else 1, Source.MEASURED,
                  f"{len(kaputt)} defekte Links auf der Startseite" if kaputt
                  else "Keine defekten Links auf der Startseite")
    else:
        sheet.skip("se_links")


# ═══════════════════════════════════════════════════════════════════
# Design & Gestaltung
# ═══════════════════════════════════════════════════════════════════

def _score_design(sheet: _Sheet, facts: dict) -> None:
    qa = facts.get("qa") or {}
    psi = facts.get("psi_mobile") or {}
    audits = (psi.get("a11y_audits") or {}) if _ok(psi) else {}

    if qa:
        sheet.set("dg_mobil", 1 if qa.get("mobile_viewport") else 0, Source.MEASURED,
                  "Viewport-Angabe im Seitenkopf vorhanden"
                  if qa.get("mobile_viewport") else "Keine Viewport-Angabe im Seitenkopf")
    else:
        sheet.skip("dg_mobil")

    # **dg_typografie: gemessen statt geschaetzt (S1.2, 24.08.2026).**
    # Lighthouse liefert `font-size`; das Kriterium liess die Schriftgroesse
    # bis dahin von einem Sprachmodell schaetzen. Ohne PageSpeed gilt es als
    # nicht erhoben — `scale` macht das selbst, wenn der Wert `None` ist.
    #
    # Die Pruefung ist binaer, also sind es 0 oder 2 Punkte. Dieselbe Bauart
    # wie `bf_kontrast`, das `color-contrast` genauso abbildet.
    if audits.get("typografie") is not None:
        sheet.scale("dg_typografie", audits.get("typografie"), Source.MEASURED,
                    "Lighthouse-Prüfung der Schriftgröße bestanden"
                    if audits.get("typografie") else
                    "Lighthouse meldet zu kleine Schrift auf Mobilgeräten")
    else:
        a11y = facts.get("a11y_browser") or {}
        klein = a11y.get("schrift_zu_klein") or 0
        geprueft = a11y.get("schrift_geprueft") or 0
        sheet.scale("dg_typografie", a11y_browser.schrift_anteil(a11y), Source.MEASURED,
                    (f"Am gerenderten Dokument gemessen: {klein} von {geprueft} "
                     f"Textstellen unter 12 px") if geprueft else "")

    # dg_aktualitaet, dg_farbsystem, dg_bildqualitaet: KI (siehe _apply_ai)


# ═══════════════════════════════════════════════════════════════════
# Conversion & Nutzerführung
# ═══════════════════════════════════════════════════════════════════

# Merkmale, die aus mehreren Beobachtungen zusammenfallen. Sie werden hier
# gebildet und nicht in der Erhebung: Fakten von vorher kennen die Einzelwerte,
# ein zusammengesetztes Feld hätten sie nie — und wären dafür abgewertet worden.
KONTAKT_ABLEITUNGEN = {
    "termin_oder_sprechzeiten": ("terminbuchung", "oeffnungszeiten"),
    "form_oder_terminbuchung": ("form", "terminbuchung"),
    "kundenservice_kontakt": ("tel_link", "mailto_link", "form", "servicekontakt"),
}


def _kontaktmerkmal(contact: dict, merkmal: str) -> bool:
    """Ein Kontaktmerkmal — einzeln beobachtet oder aus mehreren gebildet."""
    teile = KONTAKT_ABLEITUNGEN.get(merkmal)
    if teile:
        return any(contact.get(t) for t in teile)
    return bool(contact.get(merkmal))


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
        _nach_abstufung(sheet, "cv_cta", count, Source.DERIVED)
    else:
        sheet.skip("cv_cta")

    if _ok(contact):
        # Drei Beobachtungen, welche entscheidet die Klasse: Sprechzeiten in
        # der Praxis, Anfahrt im Publikumsbetrieb, Retourenweg im Shop. Vorher
        # verlor jede Praxis den Punkt für die nicht genannte Reaktionszeit —
        # ein Maßstab aus dem Handwerk.
        merkmale = kontakt_merkmale(klasse)
        sheet.set("cv_kontakt", sum(
            1 for merkmal in merkmale if _kontaktmerkmal(contact, merkmal)
        ), Source.MEASURED, teile_beleg(
            [(_kontaktmerkmal(contact, m), str(m)) for m in merkmale]
        ))
    else:
        sheet.skip("cv_kontakt")

    if _ok(trust):
        signale = _vertrauenssignale(trust, klasse)
        _nach_abstufung(sheet, "cv_vertrauen", signale, Source.DERIVED)
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
        _nach_abstufung(sheet, "ih_leistungsseiten", count)
    else:
        sheet.skip("ih_leistungsseiten")

    if _ok(freshness):
        current = freshness.get("copyright_current") or freshness.get("has_dated_content")
        jahr = freshness.get("copyright_year")
        sheet.set("ih_aktualitaet", 1 if current else 0, Source.MEASURED, teile_beleg((
            (freshness.get("copyright_current"),
             f"Copyright {jahr}" if jahr else "aktuelles Copyright"),
            (freshness.get("has_dated_content"), "datierte Inhalte"),
        )))
    else:
        sheet.skip("ih_aktualitaet")
    # ih_textqualitaet: KI (siehe _apply_ai)


# ═══════════════════════════════════════════════════════════════════
# KI-bewertete Kriterien
# ═══════════════════════════════════════════════════════════════════

def _apply_ai(sheet: _Sheet, ai: dict) -> None:
    """Trägt die KI-Bewertung ein — nur für Kriterien, die als KI markiert sind.

    **Was das Modell nicht beurteilen konnte, kostet nichts (S8.1).** Bis zum
    25.08.2026 verlangte der Prompt in diesem Fall 0 Punkte — gegen § 3.5 der
    Bewertungslogik, und im Bericht las es sich als Urteil über den Betrieb
    statt als Lücke der Prüfung. Bis zu neun Punkte für etwas, das er nicht
    getan hat.

    Unbekannte Kennungen in der Liste werden übergangen: Das Modell könnte
    etwas benennen, das kein Kriterium ist, und daran soll keine Bewertung
    scheitern.
    """
    offen = set(ai.get("nicht_beurteilbar") or []) if ai else set()
    for criterion in ai_criteria():
        value = ai.get(criterion.key) if ai else None
        if value is None or criterion.key in offen:
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

    # **Seit dem 26.08.2026 wirklich erhoben.** Der Katalog nannte diese
    # Deckelregel seit jeher; gemessen hat sie niemand, weil sie einen
    # Cookie-Vergleich vor der Einwilligung verlangt und die HTML-Erhebung
    # nur die **Signatur** eines Consent-Werkzeugs erkennt, nicht sein
    # Verhalten. Der Browserlauf klickt kein Banner an — was danach gesetzt
    # ist, ist ohne Zustimmung gesetzt.
    #
    # `_ok` haelt die alte Lage aufrecht, wenn kein Browser lief: Dann steht
    # dort `collected: False`, und es wird nichts behauptet.
    cookies = facts.get("cookies_vor_consent") or {}
    if _ok(cookies) and cookies.get("verstoss"):
        blockers.append("cookies_ohne_consent")

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
    _score_seo(sheet, facts, klasse)
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
        # **Der Beleg je Kriterium (L-151, 04.09.2026).** Der gemessene Wert,
        # der zur Punktzahl gefuehrt hat — in Klartext, nicht als Rohwert. Er
        # entsteht an der Rechenstelle, damit Zahl und Begruendung nicht
        # auseinanderlaufen koennen.
        "belege": sheet.belege,
        "blockers": blockers,
        "level": level,
    }
