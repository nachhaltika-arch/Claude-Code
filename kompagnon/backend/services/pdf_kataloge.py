"""Die festen Tabellen des Audit-Berichts (L-25).

**Warum eigene Datei, 22.08.2026.** `services/pdf_generator.py` hatte 1.424
Zeilen — davon **575 in einer einzigen Funktion**, `generate_audit_report`.
Rechtspflichten, GEO-Pruefpunkte und Fahrplan-Massnahmen: Listen, die
sich aendern, wenn sich die Rechtslage aendert — nicht, wenn sich das
Layout aendert.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph
import logging

from services.pdf_stil import BASE_TABLE_STYLE, FONT_BOLD, FONT_NORMAL, _clean_text, _get_styles

logger = logging.getLogger(__name__)


class KatalogFehlt(ValueError):
    """Das Audit stammt aus dem früheren Katalog und hat keine Einzelwerte."""


LEGAL_HEADER = ["Rechtsgrundlage", "Pflicht seit", "Betrifft", "Risiko"]


# Das TMG ist seit dem 14.05.2024 durch das Digitale-Dienste-Gesetz abgeloest.
# Der Kriterienkatalog nennt laengst „§ 5 DDG"; das PDF widersprach ihm auf
# derselben Seite.
LEGAL_ROWS = [
    ["DDG § 5 – Impressumspflicht", "seit 14.05.2024 (zuvor TMG § 5)",
     "Alle komm. Websites", "Abmahnung bis 50.000 €"],
    ["DSGVO – Datenschutz", "25.05.2018", "Websites mit EU-Besuchern", "Bußgeld bis 20 Mio €"],
    ["TDDDG §25 – Cookie", "2021/2023", "Websites mit Tracking", "Bußgeld, Abmahnungen"],
    ["BFSG – Barrierefreiheit", "28.06.2025", "Private Anbieter", "Marktaufsicht, Bußgeld"],
    ["WCAG 2.1 Level AA", "laufend", "Technische Umsetzung", "Grundlage BFSG"],
    ["Google Core Web Vitals", "Mai 2021", "Alle Websites", "Sichtbarkeitsverlust"],
]


# „Pflicht seit" war mit 25 mm die engste Spalte und traegt den laengsten
# Wert. 32 mm halten die Zeilenhoehe niedrig und bleiben mit 167 mm noch
# innerhalb der 170 mm Satzbreite (A4 minus je 20 mm Rand).
LEGAL_COL_WIDTHS = [45*mm, 32*mm, 45*mm, 45*mm]


STATUS_ERFUELLT = "erfüllt"


STATUS_OFFEN = "offen"


STATUS_UNBEKANNT = "nicht erhoben"


def _geo_status(wert):
    """``None`` heisst unbekannt — und unbekannt ist nicht dasselbe wie fehlend."""
    if wert is None:
        return STATUS_UNBEKANNT
    return STATUS_ERFUELLT if wert else STATUS_OFFEN


def rechtstabelle_zellen():
    """Die Zellen der Rechtstabelle — zu breite als umbrechender Absatz.

    reportlab bricht eine rohe Zeichenkette in einer Tabellenzelle nicht um,
    sie laeuft ueber die Spaltengrenze weiter. Im Bericht vom 15.08.2026 druckte
    sich so „seit 14.05.2024 (zuvor TMG § 5)" ueber „Alle kommerziellen
    Websites" in der Nachbarspalte; beide Angaben waren unlesbar.

    Nur ein ``Paragraph`` bricht um. Er kostet etwas Hoehe, deshalb bekommt ihn
    nur, wer ihn braucht — gemessen, nicht geraten, damit auch spaeter
    ergaenzte Zeilen richtig gesetzt werden.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    styles = _get_styles()
    innenabstand = 12  # LEFTPADDING + RIGHTPADDING aus BASE_TABLE_STYLE

    def zelle(text, breite, kopfzeile):
        schrift = FONT_BOLD if kopfzeile else FONT_NORMAL
        if stringWidth(text, schrift, 9) <= breite - innenabstand:
            return text
        stil = styles["KCZelleKopf"] if kopfzeile else styles["KCZelle"]
        return Paragraph(_clean_text(text), stil)

    zeilen = [[zelle(t, LEGAL_COL_WIDTHS[s], True)
               for s, t in enumerate(LEGAL_HEADER)]]
    zeilen += [[zelle(t, LEGAL_COL_WIDTHS[s], False) for s, t in enumerate(zeile)]
               for zeile in LEGAL_ROWS]
    return zeilen


def geo_pruefpunkte(audit_data: dict) -> list:
    """Die Prüfpunkte der GEO-Seite — nur mit dem, was erhoben wurde.

    Der Abschnitt las frueher Felder, die nie befuellt wurden (``llms_txt``,
    ``robots_ai_friendly``, ``structured_data``, ``ai_mentions``), bekam
    ueberall ``False`` und druckte fuer jeden Punkt eine Aufforderung — auch
    „GPTBot nicht blockieren" an einen Betrieb, dessen robots.txt niemanden
    sperrt. ``ai_overview`` war ausdruecklich aus einem nicht existierenden
    Feld geraten.

    Was hier ohne Messung steht, bekommt ``STATUS_UNBEKANNT`` und keine
    Empfehlung. Die Statusworte folgen der Bewertungsmatrix; Haekchen kaeme
    ohnehin niemand zu Gesicht, weil Helvetica ✓ und ✗ nicht kennt.
    """
    llms = audit_data.get("llms_txt")
    robots_ai = audit_data.get("robots_ai_friendly")
    strukturiert = audit_data.get("structured_data")
    gesperrt = audit_data.get("gesperrte_ki_crawler") or []

    def zeile(name, wert, aufforderung, erfuellt_text):
        """Eine Zeile: Aufforderung nur bei gemessener Luecke, sonst ein Hinweis.

        Die letzte Spalte bleibt nie leer — eine ueber alle Zeilen leere
        Spalte liest sich als Fehler, und genau so sah der Abschnitt vorher
        aus.
        """
        status = _geo_status(wert)
        if status == STATUS_OFFEN:
            return {"pruefpunkt": name, "status": status,
                    "empfehlung": aufforderung, "hinweis": ""}
        hinweis = (erfuellt_text if status == STATUS_ERFUELLT
                   else "Nicht Teil dieser Analyse")
        return {"pruefpunkt": name, "status": status,
                "empfehlung": "", "hinweis": hinweis}

    namen = ", ".join(gesperrt[:3]) if gesperrt else "KI-Crawler"

    return [
        zeile("llms.txt vorhanden", llms,
              "Datei unter /llms.txt anlegen", "Vorhanden und abrufbar"),
        zeile("robots.txt KI-freundlich", robots_ai,
              f"Sperre für {namen} in der robots.txt aufheben",
              "Kein KI-Crawler ausgesperrt"),
        zeile("Strukturierte Daten", strukturiert,
              "Schema.org-Auszeichnung ergänzen", "Schema.org vorhanden"),
        # Fuer beide gibt es keine Erhebung. Sie bleiben im Bericht, weil der
        # Leser wissen soll, dass es sie gibt — aber ohne Behauptung.
        zeile("KI-Erwähnungen", None, "", ""),
        zeile("Google AI Overview", None, "", ""),
    ]


def roadmap_massnahmen(audit_data: dict) -> dict:
    """Die Maßnahmen der Roadmap — je Phase, nur was der Befund hergibt.

    Die Liste war fest verdrahtet: „llms.txt anlegen", „Schema.org
    LocalBusiness einbauen", „robots.txt: GPTBot-Blockierung entfernen"
    standen in jedem Bericht.
    """
    punkte = {p["pruefpunkt"]: p for p in geo_pruefpunkte(audit_data)}
    offen = lambda name: punkte[name]["status"] == STATUS_OFFEN  # noqa: E731

    sofort = []
    if offen("llms.txt vorhanden"):
        sofort.append("llms.txt anlegen (ca. 1 Tag Aufwand)")
    if offen("Strukturierte Daten"):
        sofort.append("Schema.org-Auszeichnung einbauen")
    if offen("robots.txt KI-freundlich"):
        sofort.append(punkte["robots.txt KI-freundlich"]["empfehlung"])

    mittelfristig = ["Regelmäßige Blog-Inhalte für SEO-Autorität aufbauen"]
    if punkte["Strukturierte Daten"]["status"] == STATUS_ERFUELLT:
        mittelfristig.append("Weitere Schema.org-Typen (FAQPage, Review) ergänzen")

    return {
        "sofort": sofort,
        "mittelfristig": mittelfristig,
        # Diese drei haengen an keiner Messung und gelten fuer jeden Betrieb.
        "langfristig": [
            "Backlink-Aufbau über lokale Verzeichnisse und Branchenportale",
            "Google Business Profil optimieren und regelmäßig pflegen",
            "KI-Sichtbarkeit: Erwähnungen in Fachartikeln & Podcasts aufbauen",
        ],
    }
