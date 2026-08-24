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
    # Gilt für diese Branchenklasse nicht. Zählt ebenfalls nicht, ist aber
    # etwas anderes als ein Ausfall: „konnte nicht geprüft werden" liest sich
    # wie ein Mangel unserer Prüfung, „gilt hier nicht" wie eine Einordnung.
    NOT_APPLICABLE = "nicht_anwendbar"


SOURCE_LABELS = {
    Source.MEASURED: "gemessen",
    Source.DERIVED: "abgeleitet",
    Source.AI: "KI-Einschätzung",
    Source.NOT_COLLECTED: "nicht erhoben",
    Source.NOT_APPLICABLE: "gilt für diese Branche nicht",
}


@dataclass(frozen=True)
class Criterion:
    """Ein einzelnes Prüfkriterium."""

    key: str
    label: str
    max_points: int
    source: Source          # geplante Erhebungsart im Bestfall
    hint: str = ""          # was konkret geprüft wird — erscheint im Report
    # **Die zweite Erhebungsart, falls es eine gibt (S2.2, 24.08.2026).**
    #
    # `rc_cookie` wird auf zwei Wegen erhoben: **gemessen**, wenn ein
    # Consent-Werkzeug erkannt wird — **abgeleitet**, wenn aus „keine
    # einwilligungspflichtigen Dienste" auf „kein Banner nötig" geschlossen
    # wird. Der Katalog nannte nur den ersten.
    #
    # Das ist kein Schönheitsfehler: Kapitel 3 verspricht dem Leser, dass jede
    # Erhebungsart gekennzeichnet ist und er einer **Einschätzung**
    # widersprechen kann. Wer im Bericht „abgeleitet" liest und im Katalog
    # „gemessen", kann sich auf keines von beidem verlassen.
    #
    # Die tatsächliche Erhebungsart je Lauf steht weiterhin im Bericht
    # (`sheet.sources`); dieses Feld sagt nur, was vorkommen **darf**.
    alt_source: Optional["Source"] = None
    # Zwei Voraussetzungen, an denen die Anwendbarkeit je Branchenklasse hängt
    # (Bewertungslogik 2026.2, § 2.4). Sie stehen am Kriterium und nicht in
    # einer Klassentabelle, weil es Eigenschaften des Kriteriums sind: Eine
    # neue Klasse erbt die Regel dann von selbst.
    #
    # Setzt einen Betrieb voraus, der über die Website Kunden gewinnen will.
    # Steht dahinter kein Betrieb — ein politischer Auftritt, ein Verein, ein
    # privates Projekt —, dann gibt es kein Angebot und keine Leistungsseiten.
    # Das ist kein Mangel der Seite, sondern ein Maßstab, der nicht passt.
    assumes_business: bool = False
    # Setzt ein Einzugsgebiet voraus. Ein bundesweit arbeitender Anbieter ohne
    # Ortsbezug ist nicht schlechter auffindbar, sondern anders — ihm einen
    # fehlenden Ortsbezug vorzuhalten misst am falschen Ziel.
    assumes_local: bool = False

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
#
# **Jeder `hint` sagt, was tatsächlich geprüft wird — nicht mehr (S3).**
#
# Am 24.08.2026 versprachen zwölf Hinweise Prüfungen, die die Bewertung nicht
# durchführt. Der Hinweis erscheint im Kundenbericht; wer dort „Tap-Targets
# groß genug" liest und dafür einen Punkt verliert, sucht an der falschen
# Stelle. Gekürzt wurde, was nicht eingelöst wird:
#
#   rc_formular_dsgvo  der Link zur Datenschutzerklärung wird nicht geprüft
#   si_ssl             Domain-Übereinstimmung fließt in `valid` ein
#   si_drittanbieter   Karten werden nicht geprüft
#   tp_bilder          Dateigröße und Größenangaben sind **eine** Prüfung
#   bf_alt             geprüft wird das Vorhandensein, nicht die Güte
#   se_index           noindex hängt an der robots.txt, keine eigene Prüfung
#   se_schema          es genügt **ein** passender Zusatztyp
#   se_lokal           von den NAP-Angaben nur die Telefonnummer
#   dg_mobil           Tap-Targets werden nicht geprüft
#   ih_aktualitaet     `und` → `oder`; das Kriterium ist milder als beschrieben
#   cv_cta             gezählt wird die Anzahl, nicht die Formulierung
#   ih_textqualitaet   „Worthülsen" gestrichen — `audit_ai.py:72` untersagt dem
#                      Modell genau dieses Wort in der Ausgabe. Ein Hinweis,
#                      der es führt, verlangt, was der Prompt verbietet.
#
# **Keine Punktänderung.** Gekürzt wurde die Beschreibung, nicht der Maßstab;
# die Katalogsumme bleibt 103 (Entscheidung aus C4, Szenario B).

CATALOGUE: Tuple[Category, ...] = (
    Category(
        key="recht_compliance",
        label="Recht & Compliance",
        criteria=(
            Criterion("rc_impressum", "Impressum (§ 5 DDG)", 6, Source.MEASURED,
                      "Unterseite erreichbar und Pflichtangaben vollständig"),
            Criterion("rc_datenschutz", "Datenschutzerklärung (DSGVO)", 6, Source.MEASURED,
                      "Unterseite erreichbar und Pflichtinhalte vorhanden"),
            # **Zwei Erhebungsarten (S2.2).** Gemessen, wenn ein
            # Consent-Werkzeug erkannt wird; abgeleitet, wenn aus „keine
            # einwilligungspflichtigen Dienste" auf „kein Banner noetig"
            # geschlossen wird. Beides kommt vor, beides gehoert deklariert.
            Criterion("rc_cookie", "Cookie-Consent (TDDDG)", 4, Source.MEASURED,
                      "Consent-Tool erkannt, nicht bloß das Wort 'Cookie' — "
                      "oder kein einwilligungspflichtiger Dienst vorhanden",
                      alt_source=Source.DERIVED),
            Criterion("rc_bfsg", "Barrierefreiheitserklärung (BFSG)", 2, Source.MEASURED,
                      "Erklärung zur Barrierefreiheit verlinkt"),
            Criterion("rc_formular_dsgvo", "Formular DSGVO-konform", 2, Source.MEASURED,
                      "Einwilligungs-Checkbox am Formular"),
        ),
    ),
    Category(
        key="sicherheit",
        label="Sicherheit & Datenschutz",
        criteria=(
            Criterion("si_ssl", "TLS-Zertifikat gültig", 3, Source.MEASURED,
                      "echter Handshake und gültiges Zertifikat, Abzug bei baldigem Ablauf"),
            Criterion("si_redirect", "HTTP→HTTPS erzwungen", 2, Source.MEASURED,
                      "Redirect-Test auf der http-Variante"),
            Criterion("si_header", "Security-Header", 3, Source.MEASURED,
                      "HSTS, CSP, X-Frame-Options, X-Content-Type-Options"),
            Criterion("si_drittanbieter", "Drittanbieter ohne Einwilligung", 2, Source.MEASURED,
                      "externe Fonts, Tracking vor dem Consent"),
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
                      "modernes Format, lazy loading, Größenangaben ohne überdimensionierte Bilder"),
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
                      "Anteil der Bilder mit einem Alt-Text"),
            # **Gemessen, nicht abgeleitet (S2.1).** Der Katalog fuehrte
            # `DERIVED`, waehrend die Bewertung `MEASURED` schrieb. Seit dem
            # Anschluss der Lighthouse-Gruppe (S1.1) ist es zweifelsfrei
            # gemessen: DOM-Hierarchie plus `html-has-lang` und `label`.
            Criterion("bf_semantik", "Semantik & Struktur", 2, Source.MEASURED,
                      "saubere Überschriftenhierarchie, lang-Attribut, Labels"),
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
                      "robots.txt ohne Aussperrung, sitemap.xml, Canonical"),
            Criterion("se_schema", "Strukturierte Daten", 3, Source.MEASURED,
                      "JSON-LD vorhanden, passender Haupttyp, ein passender Zusatztyp"),
            Criterion("se_lokal", "Lokale Signale", 3, Source.MEASURED,
                      "Ort in Title oder H1, Telefonnummer als Link, Karte oder LocalBusiness",
                      assumes_local=True),
            Criterion("se_links", "Keine defekten Links", 1, Source.MEASURED,
                      "Linkprüfung über die Startseite"),
            # L-58 (a), 2026-08-21. Der Katalog hatte kein einziges Kriterium
            # für KI — kein Treffer auf ChatGPT, Perplexity oder AEO —,
            # während `audit_runner.audit_facts` die Werte seit dem 16.08.
            # bereits erhebt und das PDF sie druckt. Bewertet hat sie niemand.
            #
            # Der Name sagt **Lesbarkeit**, nicht Sichtbarkeit: Gemessen wird,
            # ob eine Maschine den Betrieb lesen *kann*. Ob sie ihn auf eine
            # Frage hin *nennt*, misst hier nichts — das ist L-58 (b), kostet
            # je Lauf Geld und ist ein eigenes Produkt.
            Criterion("se_ki_lesbar", "Lesbarkeit für KI-Systeme", 3, Source.MEASURED,
                      "KI-Crawler in robots.txt nicht ausgesperrt, llms.txt vorhanden"),
        ),
    ),
    Category(
        key="design",
        label="Design & Gestaltung",
        criteria=(
            Criterion("dg_aktualitaet", "Visuelle Aktualität", 3, Source.AI,
                      "Wirkt das Layout zeitgemäß oder veraltet?"),
            # **Gemessen statt geschätzt seit dem 24.08.2026 (S1.2).**
            # Lighthouse liefert `font-size` — die Schriftgröße wurde also
            # gemessen, während dieses Kriterium sie von einem Sprachmodell
            # schätzen ließ. Der Hinweis ist auf das gekürzt, was tatsächlich
            # geprüft wird; „Zeilenlänge" und „klare Hierarchie" versprachen
            # mehr, als eingelöst wurde (dieselbe Regel wie in S3).
            Criterion("dg_typografie", "Typografie & Lesbarkeit", 2, Source.MEASURED,
                      "Lighthouse-Audit 'font-size': lesbare Schriftgröße auf Mobilgeräten"),
            Criterion("dg_farbsystem", "Farbsystem & Konsistenz", 2, Source.AI,
                      "begrenzte Palette, erkennbare CI, ausreichender Kontrast"),
            Criterion("dg_bildqualitaet", "Bildqualität & Authentizität", 2, Source.AI,
                      "echte Betriebsfotos statt generischem Stockmaterial"),
            Criterion("dg_mobil", "Mobile Darstellung", 1, Source.MEASURED,
                      "Viewport-Angabe im Kopf der Seite"),
        ),
    ),
    Category(
        key="conversion",
        label="Conversion & Nutzerführung",
        criteria=(
            Criterion("cv_klarheit", "Klarheit above the fold", 3, Source.AI,
                      "Was, für wen, in welchem Gebiet — in fünf Sekunden erfassbar",
                      assumes_business=True),
            Criterion("cv_cta", "Primär-CTA", 3, Source.DERIVED,
                      "mindestens ein Handlungsaufruf, ab drei die volle Punktzahl",
                      assumes_business=True),
            Criterion("cv_kontakt", "Kontaktwege", 3, Source.MEASURED,
                      "Telefon klickbar, Formular schlank, Reaktionszeit benannt",
                      assumes_business=True),
            Criterion("cv_vertrauen", "Vertrauenssignale", 3, Source.DERIVED,
                      "Bewertungen, Referenzen, Qualifikations- und "
                      "Zugehörigkeitsnachweise",
                      assumes_business=True),
            Criterion("cv_angebot", "Angebots-Klarheit", 3, Source.AI,
                      "Leistungen konkret, Ablauf oder Preisrahmen, Risk Reversal",
                      assumes_business=True),
        ),
    ),
    Category(
        key="inhalt",
        label="Inhalt & Substanz",
        criteria=(
            Criterion("ih_leistungsseiten", "Eigene Leistungsseiten", 2, Source.MEASURED,
                      "je Hauptleistung eine Seite statt einer Sammelseite",
                      assumes_business=True),
            Criterion("ih_aktualitaet", "Aktualität", 1, Source.MEASURED,
                      "datierte Inhalte oder aktuelles Copyright"),
            Criterion("ih_textqualitaet", "Textqualität", 2, Source.AI,
                      "Kundennutzen statt Selbstbeschreibung",
                      assumes_business=True),
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

#: Die Rohpunktsumme, die der Katalog **haben soll**.
#:
#: Sie stand bis zum 21.08.2026 als nackte `100` in der Pruefung — und
#: widersprach damit dem Kopf dieser Datei, der ausdruecklich sagt, dass die
#: Gewichte nicht auf 100 aufgehen muessen, weil normiert wird. Beides konnte
#: nicht stimmen. Jetzt steht die Zahl hier, mit einem Grund daneben: Der
#: Waechter faengt weiterhin jede **versehentliche** Verschiebung, aber eine
#: beabsichtigte wird sichtbar und muss hier eingetragen werden.
#:
#: 2026-08-11: 100 — Freigabe nach `docs/Audit/audit-anforderungen-2026-08-11.md`
#: 2026-08-21: 103 — `se_ki_lesbar` (3 P) ergaenzt, L-58 (a). Bewusst **ohne**
#:   anderswo Gewicht wegzunehmen: Welches Kriterium dafuer leichter wird, ist
#:   eine Produktentscheidung und gehoert David. Bis dahin wiegt jedes
#:   bestehende Kriterium rechnerisch 100/103 seines bisherigen Anteils.
ERWARTETE_GESAMTPUNKTE: int = 103


# ═══════════════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════════════

# Klassen ohne Betrieb dahinter bzw. ohne Einzugsgebiet (§ 2.2 der
# Bewertungslogik 2026.2). Was daraus folgt, steht am Kriterium selbst.
KLASSE_OHNE_BETRIEB = frozenset({"K6"})
KLASSE_OHNE_EINZUGSGEBIET = frozenset({"K4", "K6"})


def ist_anwendbar(key: str, klasse: Optional[str]) -> bool:
    """Gilt dieses Kriterium für diese Branchenklasse?

    Ohne Klasse — und bei einer unbekannten — wird alles bewertet. Lieber
    vollständig messen als stillschweigend Kriterien verschlucken, deren
    Wegfall niemandem auffiele.
    """
    criterion = find_criterion(key)
    if criterion is None or not klasse:
        return True
    if criterion.assumes_business and klasse in KLASSE_OHNE_BETRIEB:
        return False
    if criterion.assumes_local and klasse in KLASSE_OHNE_EINZUGSGEBIET:
        return False
    return True


def anwendbares_maximum(klasse: Optional[str] = None) -> int:
    """Die erreichbaren Punkte dieser Klasse — gerechnet, nicht notiert.

    Die Bewertungslogik nennt in § 2.4 feste Maxima je Klasse. Die stimmen mit
    ihren eigenen Einzelwerten nicht überein (79 gegen 78 bei K6). Deshalb wird
    hier gezählt: Eine Zahl, die aus dem Katalog folgt, kann nicht veralten.
    """
    return sum(c.max_points for c in all_criteria() if ist_anwendbar(c.key, klasse))


def _collected(key: str, sources: Dict[str, Source]) -> bool:
    """Zählt dieses Kriterium in Zähler und Nenner?

    Nicht erhoben und nicht anwendbar fallen beide heraus — das eine, weil die
    Prüfung ausfiel, das andere, weil der Maßstab nicht passt. Getrennt gehalten
    werden sie nur in der Ausgabe, wo der Unterschied den Leser betrifft.
    """
    quelle = sources.get(key, Source.NOT_COLLECTED)
    return quelle not in (Source.NOT_COLLECTED, Source.NOT_APPLICABLE)


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
    klasse: Optional[str] = None,
) -> dict:
    """Gesamtauswertung: Kategorien, normierter Gesamtscore, Abdeckung.

    Der Gesamtscore ist der Anteil erreichter an erreichbaren Punkten,
    normiert auf 0–100. Nicht erhobene Kriterien reduzieren den Nenner,
    statt als Null durchzuschlagen.

    Die Abdeckung misst gegen das **anwendbare** Maximum der Branchenklasse,
    nicht gegen die vollen 100 Punkte. Sonst läse sich bei einer Seite ohne
    Betrieb eine Abdeckung von 78 %, als wäre ein Fünftel der Prüfung
    misslungen — dabei gilt es dort schlicht nicht.
    """
    categories = [score_category(cat, items, sources) for cat in CATALOGUE]

    achieved = sum(c["score"] for c in categories)
    possible = sum(c["max"] for c in categories)
    total = round(achieved / possible * 100) if possible else 0
    anwendbar = anwendbares_maximum(klasse)

    return {
        "categories": categories,
        "achieved_points": achieved,
        "possible_points": possible,
        "applicable_max": anwendbar,
        "total_score": total,
        "coverage": round(possible / anwendbar * 100) if anwendbar else 0,
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

    if TOTAL_POINTS != ERWARTETE_GESAMTPUNKTE:
        raise ValueError(
            f"Katalog ergibt {TOTAL_POINTS} statt {ERWARTETE_GESAMTPUNKTE} Punkte — "
            "entweder ist eine Gewichtung verrutscht, oder die Aenderung war "
            "gewollt und gehoert in ERWARTETE_GESAMTPUNKTE, mit Datum und Grund."
        )


_validate()
