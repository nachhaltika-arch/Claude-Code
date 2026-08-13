"""
Kriterienkatalog für das Website-Audit — einzige Wahrheitsquelle.

Bis 2026-08-11 stand die Kriterienliste dreifach im Code: im KI-Prompt, in der
Fallback-Bewertung und im Frontend. Die drei Listen sind auseinandergelaufen.
Dieses Modul hält sie einmal; Scoring, Prompt und API-Antwort leiten sich daraus ab.

Der Gesamtscore wird immer auf 0–100 normiert, egal wie die Punkte im Katalog
verteilt sind. Damit gilt:

  * Gewichte lassen sich ändern, ohne dass sie in Summe exakt 100 ergeben müssen.
  * Nicht erhobene Kriterien fallen aus Zähler UND Nenner — es wird nie eine
    fehlende Messung als "0 Punkte" verkauft.

Gewichtung freigegeben am 2026-08-11 nach docs/audit-anforderungen-2026-08-11.md.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Source(str, Enum):
    """Woher der Punktwert eines Kriteriums stammt."""

    MEASURED = "gemessen"        # deterministisch über HTTP, DOM oder API erhoben
    DERIVED = "abgeleitet"       # aus gemessenen Werten über feste Regeln berechnet
    AI = "einschaetzung"         # KI-Bewertung auf Screenshot/Text nach festem Rubric
    NOT_COLLECTED = "nicht_erhoben"  # Prüfung nicht möglich — zählt nicht in den Score


SOURCE_LABELS = {
    Source.MEASURED: "gemessen",
    Source.DERIVED: "abgeleitet",
    Source.AI: "KI-Einschätzung",
    Source.NOT_COLLECTED: "nicht erhoben",
}


@dataclass(frozen=True)
class Criterion:
    """Ein einzelnes Prüfkriterium."""

    key: str
    label: str
    max_points: int
    source: Source          # geplante Erhebungsart im Bestfall
    hint: str = ""          # was konkret geprüft wird — erscheint im Report

    @property
    def is_scored(self) -> bool:
        return self.max_points > 0


@dataclass(frozen=True)
class Category:
    """Eine Kriteriengruppe."""

    key: str
    label: str
    criteria: Tuple[Criterion, ...]

    @property
    def max_points(self) -> int:
        """Immer aus den Kriterien abgeleitet — kein manueller Deckel.

        Der frühere Code deckelte 'Inhalt & Nutzererfahrung' auf 5, obwohl die
        Kategorie sechs Kriterien à 1 Punkt hatte. Ein Kriterium war dadurch
        strukturell wertlos. Eine abgeleitete Obergrenze macht das unmöglich.
        """
        return sum(c.max_points for c in self.criteria)


# ═══════════════════════════════════════════════════════════════════
# Katalog
# ═══════════════════════════════════════════════════════════════════

CATALOGUE: Tuple[Category, ...] = (
    Category(
        key="recht_compliance",
        label="Recht & Compliance",
        criteria=(
            Criterion("rc_impressum", "Impressum (§ 5 DDG)", 6, Source.MEASURED,
                      "Unterseite erreichbar und Pflichtangaben vollständig"),
            Criterion("rc_datenschutz", "Datenschutzerklärung (DSGVO)", 6, Source.MEASURED,
                      "Unterseite erreichbar und Pflichtinhalte vorhanden"),
            Criterion("rc_cookie", "Cookie-Consent (TDDDG)", 4, Source.MEASURED,
                      "Consent-Tool erkannt, nicht bloß das Wort 'Cookie'"),
            Criterion("rc_bfsg", "Barrierefreiheitserklärung (BFSG)", 2, Source.MEASURED,
                      "Erklärung zur Barrierefreiheit verlinkt"),
            Criterion("rc_formular_dsgvo", "Formular DSGVO-konform", 2, Source.MEASURED,
                      "Einwilligungs-Checkbox und Link zur Datenschutzerklärung"),
        ),
    ),
    Category(
        key="sicherheit",
        label="Sicherheit & Datenschutz",
        criteria=(
            Criterion("si_ssl", "TLS-Zertifikat gültig", 3, Source.MEASURED,
                      "echter Handshake, Gültigkeit und Domain-Übereinstimmung"),
            Criterion("si_redirect", "HTTP→HTTPS erzwungen", 2, Source.MEASURED,
                      "Redirect-Test auf der http-Variante"),
            Criterion("si_header", "Security-Header", 3, Source.MEASURED,
                      "HSTS, CSP, X-Frame-Options, X-Content-Type-Options"),
            Criterion("si_drittanbieter", "Drittanbieter ohne Einwilligung", 2, Source.MEASURED,
                      "externe Fonts, Karten und Tracking vor dem Consent"),
        ),
    ),
    Category(
        key="performance",
        label="Performance & Core Web Vitals",
        criteria=(
            Criterion("tp_lcp", "LCP (Ladezeit Hauptinhalt)", 4, Source.MEASURED,
                      "PageSpeed Insights"),
            Criterion("tp_cls", "CLS (Layout-Stabilität)", 3, Source.MEASURED,
                      "PageSpeed Insights"),
            Criterion("tp_inp", "INP (Interaktionszeit)", 2, Source.MEASURED,
                      "CrUX-Felddaten — im Labor nicht messbar"),
            Criterion("tp_mobile", "Mobile-Performance", 3, Source.MEASURED,
                      "eigener PageSpeed-Lauf mit Strategie 'mobile'"),
            Criterion("tp_bilder", "Bildoptimierung", 3, Source.MEASURED,
                      "Format, Dateigröße, lazy loading, feste Dimensionen"),
        ),
    ),
    Category(
        key="barrierefreiheit",
        label="Barrierefreiheit (WCAG/BFSG)",
        criteria=(
            Criterion("bf_lighthouse", "Lighthouse-Accessibility-Score", 3, Source.MEASURED,
                      "Gesamtwert der Lighthouse-Barrierefreiheitsprüfung"),
            Criterion("bf_kontrast", "Farbkontraste (WCAG AA)", 2, Source.MEASURED,
                      "Lighthouse-Audit 'color-contrast'"),
            Criterion("bf_alt", "Alt-Texte der Inhaltsbilder", 2, Source.MEASURED,
                      "Anteil der Bilder mit sinnvollem Alt-Text"),
            Criterion("bf_semantik", "Semantik & Struktur", 2, Source.DERIVED,
                      "genau eine H1, saubere Hierarchie, lang-Attribut, Labels"),
            Criterion("bf_tastatur", "Tastaturbedienung", 1, Source.DERIVED,
                      "Skip-Link, Fokus-Reihenfolge, keine Tastaturfallen"),
        ),
    ),
    Category(
        key="seo",
        label="SEO & Auffindbarkeit",
        criteria=(
            Criterion("se_meta", "Title & Meta-Description", 3, Source.MEASURED,
                      "vorhanden, sinnvolle Länge, Ort und Leistung enthalten"),
            Criterion("se_struktur", "Überschriften & Content-Tiefe", 2, Source.MEASURED,
                      "H2-Gliederung und ausreichender Textumfang"),
            Criterion("se_index", "Indexierbarkeit", 3, Source.MEASURED,
                      "robots.txt, sitemap.xml, Canonical, kein versehentliches noindex"),
            Criterion("se_schema", "Strukturierte Daten", 3, Source.MEASURED,
                      "JSON-LD, LocalBusiness, FAQ, Bewertungen"),
            Criterion("se_lokal", "Lokale Signale", 3, Source.MEASURED,
                      "Ort in Title/H1, NAP-Angaben, Kartenverknüpfung"),
            Criterion("se_links", "Keine defekten Links", 1, Source.MEASURED,
                      "Linkprüfung über die Startseite"),
        ),
    ),
    Category(
        key="design",
        label="Design & Gestaltung",
        criteria=(
            Criterion("dg_aktualitaet", "Visuelle Aktualität", 3, Source.AI,
                      "Wirkt das Layout zeitgemäß oder veraltet?"),
            Criterion("dg_typografie", "Typografie & Lesbarkeit", 2, Source.AI,
                      "Schriftgrößen, Zeilenlänge, klare Hierarchie"),
            Criterion("dg_farbsystem", "Farbsystem & Konsistenz", 2, Source.AI,
                      "begrenzte Palette, erkennbare CI, ausreichender Kontrast"),
            Criterion("dg_bildqualitaet", "Bildqualität & Authentizität", 2, Source.AI,
                      "echte Betriebsfotos statt generischem Stockmaterial"),
            Criterion("dg_mobil", "Mobile Darstellung", 1, Source.MEASURED,
                      "Viewport gesetzt, Tap-Targets groß genug"),
        ),
    ),
    Category(
        key="conversion",
        label="Conversion & Nutzerführung",
        criteria=(
            Criterion("cv_klarheit", "Klarheit above the fold", 3, Source.AI,
                      "Was, für wen, in welchem Gebiet — in fünf Sekunden erfassbar"),
            Criterion("cv_cta", "Primär-CTA", 3, Source.DERIVED,
                      "vorhanden, ergebnisorientiert, im Verlauf wiederholt"),
            Criterion("cv_kontakt", "Kontaktwege", 3, Source.MEASURED,
                      "Telefon klickbar, Formular schlank, Reaktionszeit benannt"),
            Criterion("cv_vertrauen", "Vertrauenssignale", 3, Source.DERIVED,
                      "Bewertungen, Referenzen, Zertifikate, Meisterbetrieb"),
            Criterion("cv_angebot", "Angebots-Klarheit", 3, Source.AI,
                      "Leistungen konkret, Ablauf oder Preisrahmen, Risk Reversal"),
        ),
    ),
    Category(
        key="inhalt",
        label="Inhalt & Substanz",
        criteria=(
            Criterion("ih_leistungsseiten", "Eigene Leistungsseiten", 2, Source.MEASURED,
                      "je Gewerk eine Seite statt einer Sammelseite"),
            Criterion("ih_aktualitaet", "Aktualität", 1, Source.MEASURED,
                      "datierte Inhalte, kein veraltetes Copyright"),
            Criterion("ih_textqualitaet", "Textqualität", 2, Source.AI,
                      "Kundennutzen statt Selbstbeschreibung, keine Worthülsen"),
        ),
    ),
)


# Infrastruktur — reine Information für die Angebotskalkulation, kein Score.
# 'ho_backup' ist entfallen: von außen prinzipiell nicht prüfbar.
INFRASTRUCTURE: Tuple[Criterion, ...] = (
    Criterion("ho_anbieter", "Hosting-Anbieter identifizierbar", 0, Source.MEASURED,
              "IP-/ASN-Lookup"),
    Criterion("ho_uptime", "Erreichbarkeit", 0, Source.MEASURED,
              "HTTP-Status der Startseite"),
    Criterion("ho_cdn", "CDN aktiv", 0, Source.MEASURED,
              "CDN-Signaturen in den Response-Headern"),
    Criterion("ho_cms", "CMS / Tech-Stack erkannt", 0, Source.MEASURED,
              "Technologie-Signaturen in HTML und Headern"),
)


LEVELS: Tuple[Tuple[int, str], ...] = (
    (95, "Homepage Standard Platin"),
    (85, "Homepage Standard Gold"),
    (70, "Homepage Standard Silber"),
    (50, "Homepage Standard Bronze"),
    (0, "Nicht konform"),
)

NON_COMPLIANT = "Nicht konform"
BRONZE = "Homepage Standard Bronze"


# ═══════════════════════════════════════════════════════════════════
# Zugriffshilfen
# ═══════════════════════════════════════════════════════════════════

def all_criteria() -> List[Criterion]:
    """Alle bewerteten Kriterien über alle Kategorien."""
    return [c for cat in CATALOGUE for c in cat.criteria]


def item_keys() -> List[str]:
    """Schlüssel aller Kriterien inklusive Infrastruktur (für DB und API)."""
    return [c.key for c in all_criteria()] + [c.key for c in INFRASTRUCTURE]


def find_criterion(key: str) -> Optional[Criterion]:
    for c in list(all_criteria()) + list(INFRASTRUCTURE):
        if c.key == key:
            return c
    return None


def category_of(key: str) -> Optional[Category]:
    for cat in CATALOGUE:
        if any(c.key == key for c in cat.criteria):
            return cat
    return None


def ai_criteria() -> List[Criterion]:
    """Kriterien, die tatsächlich eine KI-Bewertung brauchen.

    Alles andere wird deterministisch erhoben und darf nicht an die KI gehen —
    sonst rät sie wieder Werte, die längst gemessen sind.
    """
    return [c for c in all_criteria() if c.source == Source.AI]


TOTAL_POINTS: int = sum(cat.max_points for cat in CATALOGUE)


# ═══════════════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════════════

def _collected(key: str, sources: Dict[str, Source]) -> bool:
    return sources.get(key, Source.NOT_COLLECTED) != Source.NOT_COLLECTED


def _clamp(value, maximum: int) -> int:
    try:
        v = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, min(v, maximum))


def score_category(
    category: Category,
    items: Dict[str, int],
    sources: Dict[str, Source],
) -> dict:
    """Punkte einer Kategorie — nicht erhobene Kriterien fallen heraus."""
    achieved = 0
    possible = 0
    missing: List[str] = []

    for crit in category.criteria:
        if _collected(crit.key, sources):
            achieved += _clamp(items.get(crit.key, 0), crit.max_points)
            possible += crit.max_points
        else:
            missing.append(crit.key)

    return {
        "key": category.key,
        "label": category.label,
        "score": achieved,
        "max": possible,
        "nominal_max": category.max_points,
        "not_collected": missing,
        "percent": round(achieved / possible * 100) if possible else None,
    }


def score_all(
    items: Dict[str, int],
    sources: Dict[str, Source],
) -> dict:
    """Gesamtauswertung: Kategorien, normierter Gesamtscore, Abdeckung.

    Der Gesamtscore ist der Anteil erreichter an erreichbaren Punkten,
    normiert auf 0–100. Nicht erhobene Kriterien reduzieren den Nenner,
    statt als Null durchzuschlagen.
    """
    categories = [score_category(cat, items, sources) for cat in CATALOGUE]

    achieved = sum(c["score"] for c in categories)
    possible = sum(c["max"] for c in categories)
    total = round(achieved / possible * 100) if possible else 0

    return {
        "categories": categories,
        "achieved_points": achieved,
        "possible_points": possible,
        "total_score": total,
        "coverage": round(possible / TOTAL_POINTS * 100) if TOTAL_POINTS else 0,
    }


# ═══════════════════════════════════════════════════════════════════
# K.-o.-Kriterien
# ═══════════════════════════════════════════════════════════════════

BLOCKING_CRITICAL = frozenset({
    "kein_impressum", "keine_datenschutzerklaerung", "kein_gueltiges_tls",
})
BLOCKING_MAJOR = frozenset({"tracking_ohne_consent", "cookies_ohne_consent"})

BLOCKER_LABELS = {
    "kein_impressum": "Kein erreichbares Impressum (§ 5 DDG)",
    "keine_datenschutzerklaerung": "Keine erreichbare Datenschutzerklärung (Art. 13 DSGVO)",
    "kein_gueltiges_tls": "Kein gültiges TLS-Zertifikat",
    "tracking_ohne_consent": "Tracking oder externe Dienste ohne Einwilligung",
    "cookies_ohne_consent": "Cookies werden vor der Einwilligung gesetzt",
}


def _cap_at(level: str, ceiling: str) -> str:
    order = [lbl for _, lbl in LEVELS][::-1]  # schlechtestes zuerst
    return level if order.index(level) <= order.index(ceiling) else ceiling


def determine_level(total_score: int, blockers: Optional[List[str]] = None) -> str:
    """Level aus dem Score, gedeckelt durch K.-o.-Kriterien.

    Ohne Deckel könnte eine Website ohne Impressum rechnerisch 'Silber'
    erreichen. Ein Report, der Rechtsverstöße prämiert, ist als Verkaufs-
    unterlage nicht haltbar.
    """
    level = next(lbl for threshold, lbl in LEVELS if total_score >= threshold)
    if not blockers:
        return level

    if any(b in BLOCKING_CRITICAL for b in blockers):
        return NON_COMPLIANT
    if any(b in BLOCKING_MAJOR for b in blockers):
        return _cap_at(level, BRONZE)
    return level


# ═══════════════════════════════════════════════════════════════════
# Konsistenzprüfung beim Import
# ═══════════════════════════════════════════════════════════════════

def _validate() -> None:
    keys = item_keys()
    duplicates = {k for k in keys if keys.count(k) > 1}
    if duplicates:
        raise ValueError(f"Doppelte Kriterien-Schlüssel im Katalog: {sorted(duplicates)}")

    for crit in all_criteria():
        if crit.max_points <= 0:
            raise ValueError(f"Bewertetes Kriterium ohne Punkte: {crit.key}")

    if TOTAL_POINTS != 100:
        raise ValueError(
            f"Katalog ergibt {TOTAL_POINTS} statt 100 Punkte — Gewichtung prüfen"
        )


_validate()
