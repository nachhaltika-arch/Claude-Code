"""
PDF Audit Report Generator — Homepage Standard 2025
Generates a professional multi-page PDF using ReportLab.
"""
import json
import logging
import os
import unicodedata
import math
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable, Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


from services.audit_criteria import BLOCKER_LABELS, CATALOGUE, SOURCE_LABELS, Source
from services.audit_industry_map import KLASSEN

logger = logging.getLogger(__name__)

# Kurzform der Quellenangabe für die enge PDF-Spalte
SOURCE_SHORT = {
    Source.MEASURED.value: "gemessen",
    Source.DERIVED.value: "abgeleitet",
    Source.AI.value: "KI",
    Source.NOT_COLLECTED.value: "n. erhoben",
}


class KatalogFehlt(ValueError):
    """Das Audit stammt aus dem früheren Katalog und hat keine Einzelwerte."""


# ═══════════════════════════════════════════════════════════
# Schriftregistrierung
# ═══════════════════════════════════════════════════════════

# Noto Sans liegt im Repo unter assets/fonts. Das ist die Schrift der CI, und
# als einzige deckt sie ab, was in diesem Bericht vorkommt.
#
# Vorher stand hier die Suche nach DejaVu mit dem Kommentar „for full
# Unicode/Umlaut support". Reportlab 4 liefert DejaVu aber nicht mehr mit, der
# Aufruf lief jedes Mal in den Fehlerzweig, und jedes bisher erzeugte PDF ist
# in Helvetica gesetzt. Das mitgelieferte Vera waere greifbar gewesen, kennt
# aber den Pfeil in „HTTP→HTTPS erzwungen" nicht.
SCHRIFT_ORDNER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")


def _register_fonts():
    """Registriert Noto Sans; faellt zurueck, wenn die Dateien fehlen.

    Die Rueckfallkette ist bewusst kurz und endet bei Helvetica. Sie greift
    nur, wenn jemand die TTFs aus dem Repo entfernt — dann sieht das PDF
    anders aus, bleibt aber lesbar, statt beim Erzeugen zu scheitern.
    """
    import reportlab

    reportlab_fonts = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    kandidaten = [
        (SCHRIFT_ORDNER, "NotoSans", "NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
        (reportlab_fonts, "DejaVu", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
    ]
    for ordner, name, normal, fett in kandidaten:
        try:
            pdfmetrics.registerFont(TTFont(name, os.path.join(ordner, normal)))
            pdfmetrics.registerFont(TTFont(f"{name}-Bold", os.path.join(ordner, fett)))
            pdfmetrics.registerFontFamily(name, normal=name, bold=f"{name}-Bold")
            return name, f"{name}-Bold"
        except Exception as e:  # noqa: BLE001 — naechster Kandidat
            logger.warning(f"Schrift {name} nicht nutzbar: {e}")
            continue

    logger.warning("Keine TrueType-Schrift gefunden — PDF faellt auf Helvetica "
                   "zurueck; Sonderzeichen wie → fehlen dort.")
    return "Helvetica", "Helvetica-Bold"

FONT_NORMAL, FONT_BOLD = _register_fonts()


# Zeichen, die keine der in Frage kommenden Schriften hat, mit dem naechsten
# lesbaren Ersatz. Der Pfeil steht im Kriterium „HTTP→HTTPS erzwungen" und
# verschwand in Noto Sans spurlos — mitten im Wort, ohne Fehlermeldung.
ZEICHEN_ERSATZ = {
    "→": "->", "←": "<-", "↔": "<->", "⇒": "=>", "⇐": "<=",
    "↑": "^", "↓": "v",
    "✓": "+", "✔": "+", "✗": "x", "✘": "x",
    "●": "*", "◐": "*", "○": "-", "▪": "-", "▸": ">",
    "≥": ">=", "≤": "<=", "≠": "!=", "≈": "~",
    "…": "...", "™": "(TM)", "№": "Nr.",
}


def _unterstuetzte_zeichen() -> set:
    """Welche Zeichen die gewaehlte Schrift tatsaechlich zeichnen kann."""
    try:
        for name in (FONT_NORMAL, FONT_BOLD):
            schrift = pdfmetrics.getFont(name)
            tabelle = getattr(getattr(schrift, "face", None), "charToGlyph", None)
            if tabelle:
                return set(tabelle)
    except Exception:  # noqa: BLE001
        pass
    # Helvetica & Co. sind Type-1-Schriften ohne cmap. Sie koennen genau das,
    # was WinAnsi (cp1252) abdeckt.
    zeichen = set()
    for code in range(0x20, 0x2200):
        try:
            chr(code).encode("cp1252")
        except UnicodeEncodeError:
            continue
        zeichen.add(code)
    return zeichen


ZEICHENVORRAT = _unterstuetzte_zeichen()


def _clean_text(text):
    """Normalisiert Text und ersetzt, was die Schrift nicht zeichnen kann.

    Ohne diesen Schritt fehlt ein nicht vorhandenes Zeichen im PDF einfach —
    kein Kaestchen, keine Warnung, nur eine Luecke mitten im Wort. Das trifft
    nicht nur feste Beschriftungen: Zusammenfassung, Mangelliste und
    Empfehlungen kommen aus der KI und koennen jedes Zeichen enthalten.
    """
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize("NFC", text)

    if all(ord(z) in ZEICHENVORRAT for z in text):
        return text

    heraus = []
    for zeichen in text:
        if ord(zeichen) in ZEICHENVORRAT:
            heraus.append(zeichen)
            continue
        ersatz = ZEICHEN_ERSATZ.get(zeichen)
        if ersatz is None:
            # Zerlegen hilft bei zusammengesetzten Zeichen; bleibt danach
            # etwas Unzeichenbares uebrig, faellt es weg.
            ersatz = "".join(
                z for z in unicodedata.normalize("NFKD", zeichen)
                if ord(z) in ZEICHENVORRAT)
        heraus.append(ersatz)
    return "".join(heraus)

# ═══════════════════════════════════════════════════════════
# Colors
# ═══════════════════════════════════════════════════════════

# Die Werte kommen aus services/brand.py, dem Gegenstueck zu tokens.css.
# Hier stand eine vierte, voellig eigene Palette (#2c3e50, #f39c12, #e74c3c —
# Flat-UI-Toene). Widget, Mail, Berichtsseite und PDF sahen damit nach vier
# verschiedenen Absendern aus.
from services import brand  # noqa: E402

KC_DARK = colors.HexColor(brand.DARK)
KC_MID = colors.HexColor(brand.MID)
KC_YELLOW = colors.HexColor(brand.YELLOW)
KC_LIGHT = colors.HexColor(brand.SURFACE)
KC_WHITE = colors.white
KC_BORDER = colors.HexColor(brand.BORDER)
KC_TEXT = colors.HexColor(brand.TEXT)
KC_TEXT_60 = colors.HexColor(brand.TEXT_60)
KC_SUCCESS = colors.HexColor(brand.SUCCESS)
KC_WARNING = colors.HexColor(brand.WARN)
KC_DANGER = colors.HexColor(brand.ERROR)
KC_ROT = KC_DANGER
KC_ERROR_BG = colors.HexColor(brand.ERROR_BG)

# Die Stufe als Medaillenton — aber nur als schmaler Balken neben dem
# Abzeichen, nicht als dessen Flaeche. Als Flaeche trug sie weisse Schrift:
# auf Silber (#C0C0C0) und Gold (#FFD700) war die Stufe praktisch unlesbar.
LEVEL_ACCENTS = {
    "Homepage Standard Platin": colors.HexColor("#8E9BA6"),
    "Homepage Standard Gold": colors.HexColor("#C9A227"),
    "Homepage Standard Silber": colors.HexColor("#9AA5AC"),
    "Homepage Standard Bronze": colors.HexColor("#B0763A"),
    "Nicht konform": KC_DANGER,
}

# ═══════════════════════════════════════════════════════════
# Styles
# ═══════════════════════════════════════════════════════════

def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "KCTitle", parent=styles["Title"],
        fontName=FONT_BOLD, fontSize=28, leading=34,
        textColor=KC_DARK, alignment=TA_CENTER, spaceAfter=6*mm,
    ))
    styles.add(ParagraphStyle(
        "KCSubtitle", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=14, leading=18,
        textColor=KC_TEXT_60, alignment=TA_CENTER, spaceAfter=10*mm,
    ))
    styles.add(ParagraphStyle(
        "KCHeading", parent=styles["Heading2"],
        fontName=FONT_BOLD, fontSize=16, leading=20,
        textColor=KC_DARK, spaceBefore=8*mm, spaceAfter=4*mm,
    ))
    styles.add(ParagraphStyle(
        "KCBody", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=10, leading=14,
        textColor=KC_DARK, spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        "KCSmall", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=8, leading=10,
        textColor=KC_TEXT_60,
    ))
    styles.add(ParagraphStyle(
        "KCCenter", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=10, leading=14,
        textColor=KC_DARK, alignment=TA_CENTER,
    ))
    # Tabellenzellen, die umbrechen muessen. Groesse, Schrift und Farbe wie in
    # BASE_TABLE_STYLE, damit eine umbrechende Zelle neben einer rohen nicht
    # auffaellt. Die Farbe ist KC_TEXT (schwarz) und nicht KC_DARK: Der Stil
    # setzt fuer den Tabellenkoerper keine Textfarbe, es gilt also Schwarz —
    # mit KC_DARK stand die umbrochene Zelle sichtbar in Teal daneben.
    styles.add(ParagraphStyle(
        "KCZelle", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=9, leading=11,
        textColor=KC_TEXT,
    ))
    styles.add(ParagraphStyle(
        "KCZelleKopf", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=9, leading=11,
        textColor=KC_WHITE,
    ))
    styles.add(ParagraphStyle(
        "KCBold", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=10, leading=14,
        textColor=KC_DARK,
    ))
    # Eigener Stil fuer die grosse Zahl. Sie stand vorher als <font size="48">
    # in einem Absatz mit leading=14 — die Glyphen liefen aus der Zeilenbox
    # und wurden vom naechsten Element ueberzeichnet.
    styles.add(ParagraphStyle(
        "KCScore", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=52, leading=60,
        textColor=KC_DARK, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "KCWortmarke", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=11, leading=14,
        textColor=KC_WHITE, alignment=TA_CENTER,
    ))
    return styles


def _marken_band(styles) -> Table:
    """Schmales Band in Pantone 3165 mit der Wortmarke.

    Das Deckblatt trug bisher ueberhaupt kein Markenzeichen — nur eine
    graue Ueberschrift.
    """
    zelle = Paragraph(
        f'KOMPAGNON<font color="{KC_YELLOW.hexval()}">.</font>'
        f'<font size="8" color="{KC_WHITE.hexval()}">'
        f'&nbsp;&nbsp;HOMEPAGE STANDARD</font>',
        styles["KCWortmarke"])
    band = Table([[zelle]], colWidths=[170*mm])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), KC_DARK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return band


def _stufen_abzeichen(level: str) -> Table:
    """Die erreichte Stufe.

    Die Flaeche war frueher der Medaillenton mit weisser Schrift — auf Silber
    (#C0C0C0) und Gold (#FFD700) war die Stufe damit kaum zu lesen. Jetzt
    traegt sie Pantone 3165 mit weisser Schrift, und der Medaillenton steht
    als schmaler Balken davor.
    """
    akzent = LEVEL_ACCENTS.get(level, KC_DANGER)
    text = Paragraph(
        f'<font color="{KC_WHITE.hexval()}"><b>{_clean_text(level)}</b></font>',
        ParagraphStyle("abzeichen", fontName=FONT_BOLD, fontSize=14,
                       leading=18, alignment=TA_CENTER, textColor=KC_WHITE))
    tabelle = Table([["", text]], colWidths=[5*mm, 115*mm])
    tabelle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), akzent),
        ("BACKGROUND", (1, 0), (1, 0), KC_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
    ]))
    tabelle.hAlign = "CENTER"
    return tabelle


# ═══════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════

def _safe(val, default="-"):
    if val is None:
        return _clean_text(str(default))
    return _clean_text(str(val))


# „O", „+" und „-" standen fuer konform, teilweise und nicht konform. Selbst
# mit Legende liest niemand ein „O" als Bestnote — es sieht aus wie eine Null.
#
# Haken und Kreuz waeren die naheliegende Loesung, sind hier aber nicht zu
# haben: `_register_fonts` sucht DejaVu, und reportlab 4.5 liefert das nicht
# mehr mit (nur noch Vera). Die Registrierung faellt also still auf Helvetica
# zurueck, und Helvetica kennt weder ✓ noch ✗ — sie kaemen als leere Kaestchen.
# Ein Wort braucht keine Schriftwette und erfuellt die Guideline ohnehin
# besser: Status immer durch Farbe *und* Text.
STATUS_ZEICHEN = {
    "konform":   "erfüllt",
    "teilweise": "teils",
    "offen":     "offen",
}
STATUS_FARBEN = {
    "konform": KC_SUCCESS,
    "teilweise": KC_WARNING,
    "offen": KC_DANGER,
}


def _score_status(score, max_pts):
    """Das Zeichen fuer die Statusspalte."""
    if max_pts == 0:
        return STATUS_ZEICHEN["konform"]
    pct = score / max_pts
    if pct >= 0.8:
        return STATUS_ZEICHEN["konform"]
    if pct >= 0.4:
        return STATUS_ZEICHEN["teilweise"]
    return STATUS_ZEICHEN["offen"]


def _status_color(status):
    for schluessel, zeichen in STATUS_ZEICHEN.items():
        if status == zeichen:
            return STATUS_FARBEN[schluessel]
    return KC_TEXT_60


def _parse_json_field(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


# ═══════════════════════════════════════════════════════════
# Table helpers
# ═══════════════════════════════════════════════════════════

BASE_TABLE_STYLE = [
    ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("FONTSIZE", (0, 1), (-1, -1), 9),
    ("FONTNAME", (0, 1), (-1, -1), FONT_NORMAL),
    ("BACKGROUND", (0, 0), (-1, 0), KC_DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), KC_WHITE),
    ("ALIGN", (0, 0), (-1, 0), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.5, KC_BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]


def _stil_ohne_kopfzeile(zeilen: int) -> list:
    """Stil fuer Tabellen, deren erste Zeile schon Inhalt ist.

    ``BASE_TABLE_STYLE`` faerbt Zeile 0 als Kopf: dunkle Flaeche, weisse
    Schrift. Wo die erste Zeile aber ein echter Wert ist, legte die
    Zebra-Schleife danach noch eine helle Flaeche darueber — weisse Schrift
    auf Hellgrau. Im Auditprotokoll war die erste Zeile („Website-URL") damit
    schlicht nicht zu lesen.
    """
    stil = [
        ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
        ("FONTNAME", (1, 0), (-1, -1), FONT_NORMAL),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), KC_TEXT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, KC_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(zeilen):
        if i % 2 == 0:
            stil.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
    return stil


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


STATUS_ERFUELLT = "erfüllt"
STATUS_OFFEN = "offen"
STATUS_UNBEKANNT = "nicht erhoben"


def _geo_status(wert):
    """``None`` heisst unbekannt — und unbekannt ist nicht dasselbe wie fehlend."""
    if wert is None:
        return STATUS_UNBEKANNT
    return STATUS_ERFUELLT if wert else STATUS_OFFEN


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


def _category_table_style(n_rows):
    style = list(BASE_TABLE_STYLE)
    for i in range(1, n_rows + 1):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
    return TableStyle(style)


# ═══════════════════════════════════════════════════════════
# Page footer
# ═══════════════════════════════════════════════════════════

def _footer(canvas_obj, doc):
    """Fusszeile auf jeder Seite.

    Hier stand fest „Audit 2025". Ein Bericht, den jemand 2026 in der Hand
    hält, datiert sich damit selbst ins Vorjahr — und das auf jeder Seite.
    Das Jahr kommt jetzt vom Dokument, gesetzt aus dem Auditdatum.
    """
    canvas_obj.saveState()
    canvas_obj.setFont(FONT_NORMAL, 7)
    canvas_obj.setFillColor(KC_TEXT_60)
    w, _h = A4
    jahr = getattr(doc, "kc_jahr", datetime.utcnow().year)
    # Dünner Markenstrich über der Fusszeile
    canvas_obj.setStrokeColor(KC_BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20*mm, 15*mm, w - 20*mm, 15*mm)
    canvas_obj.drawString(20*mm, 10*mm,
        _clean_text(f"KOMPAGNON Homepage Standard · Audit {jahr} · Seite {doc.page}"))
    canvas_obj.drawRightString(w - 20*mm, 10*mm,
        _clean_text("Dieses Audit ersetzt keine Rechtsberatung."))
    canvas_obj.restoreState()


# ═══════════════════════════════════════════════════════════
# Chart generators (matplotlib)
# ═══════════════════════════════════════════════════════════

def _matplotlib_schrift(plt) -> None:
    """Gibt den Diagrammen dieselbe Schrift wie dem Text.

    Ohne das setzt matplotlib seine eigene Standardschrift, und die
    Achsenbeschriftung des Radars faellt sichtbar aus dem Rest heraus.
    """
    datei = os.path.join(SCHRIFT_ORDNER, "NotoSans-Regular.ttf")
    if not os.path.exists(datei):
        return
    try:
        from matplotlib import font_manager

        font_manager.fontManager.addfont(datei)
        plt.rcParams["font.family"] = font_manager.FontProperties(
            fname=datei).get_name()
    except Exception as e:  # noqa: BLE001 — Standardschrift ist kein Beinbruch
        logger.warning(f"Diagrammschrift nicht gesetzt: {e}")


def generate_radar_chart(axes: list) -> bytes:
    """Netzdiagramm über die Kategorien des Katalogs.

    Erwartet [(Beschriftung, Wert 0-10), …] — die Achsenzahl folgt dem Katalog,
    statt wie früher auf sechs feste Kategorien verdrahtet zu sein.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _matplotlib_schrift(plt)

    if not axes:
        axes = [("Keine Daten", 0)]

    labels = [a[0] for a in axes]
    values = [float(a[1] or 0) for a in axes]

    N = len(labels)
    angles = [2 * math.pi * i / N for i in range(N)]
    angles_closed = angles + [angles[0]]
    values_closed = values + [values[0]]

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Die Werte kommen als Zehntel der Zielerreichung herein (score/max*10).
    # Die Ringe trugen deshalb „2, 4, 6, 8, 10" ohne Einheit — eine Zahl, die
    # weder Punkte noch Prozent war. Beschriftet wird jetzt, was gemeint ist.
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"],
                       fontsize=6, color=brand.TEXT_30)
    ax.yaxis.grid(True, color=brand.BORDER, linewidth=0.7)
    ax.xaxis.grid(True, color=brand.BORDER, linewidth=0.7)
    ax.spines["polar"].set_color(brand.BORDER)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=6.5, color=brand.DARK)

    ax.plot(angles_closed, values_closed, color=brand.DARK, linewidth=1.8)
    ax.fill(angles_closed, values_closed, color=brand.MID, alpha=0.30)

    plt.tight_layout(pad=1.2)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def generate_donut_chart(positions: dict):
    """Keyword-Positionen als Ring. Gibt PNG-Bytes zurück — oder ``None``.

    Ohne Daten zeichnete diese Funktion vier gleich grosse Viertel und
    beschriftete jedes mit „25 %". Im Bericht stand damit eine erfundene
    Verteilung, die der Empfaenger als Messergebnis liest — bei einem Audit,
    das Keyword-Positionen ueberhaupt nicht erhebt. Es gibt jetzt kein
    Platzhalter-Diagramm mehr: liegen keine Daten vor, faellt der Ring weg und
    der Aufrufer schreibt hin, dass nichts erhoben wurde.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _matplotlib_schrift(plt)

    labels = ["Top 10", "11–20", "21–50", "51–100"]
    values = [
        positions.get("top10", 0),
        positions.get("11_20", 0),
        positions.get("21_50", 0),
        positions.get("51_100", 0),
    ]
    if sum(values) == 0:
        return None

    palette = [brand.SUCCESS, brand.MID, brand.WARN, brand.ERROR]

    fig, ax = plt.subplots(figsize=(4, 4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=palette,
        autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
        pctdistance=0.78,
        startangle=90,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )
    for t in texts:
        t.set_fontsize(8)
        t.set_color(brand.DARK)
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color("white")
        at.set_fontweight("bold")

    plt.tight_layout(pad=0.5)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════
# Main generator
# ═══════════════════════════════════════════════════════════

def build_scorecard(items: dict, sources: dict, styles: dict) -> tuple:
    """Bewertungsmatrix: Kopfzeile je Kategorie plus eine Zeile je Kriterium.

    Die Zeilenwerte stammen aus der Einzelbewertung. Früher wurde der
    Kategorie-Score proportional auf die Kriterien verteilt — die Zahlen pro
    Zeile waren also gerechnet, nicht gemessen.

    Nicht erhobene Kriterien erscheinen mit Gedankenstrich und zählen weder
    in den erreichten noch in den möglichen Punkten der Kategorie.
    """
    header = ["ID", "Pr\u00fcfbereich", "Quelle", "Max.", "Ist", "Status"]
    rows = []

    for kategorie in CATALOGUE:
        erhoben = [c for c in kategorie.criteria
                   if sources.get(c.key, Source.NOT_COLLECTED.value)
                   != Source.NOT_COLLECTED.value]
        erreicht = sum(int(items.get(c.key, 0) or 0) for c in erhoben)
        moeglich = sum(c.max_points for c in erhoben)

        kopf = f"{kategorie.label} (max. {kategorie.max_points} Pkt.)"
        if moeglich < kategorie.max_points:
            kopf += f" \u2013 {moeglich} Pkt. pr\u00fcfbar"

        rows.append([
            Paragraph(f'<b>{_clean_text(kopf)}</b>', styles["KCBold"]),
            "", "", "",
            Paragraph(f'<b>{erreicht} / {moeglich}</b>', styles["KCBold"]),
            "",
        ])

        praefix = kategorie.criteria[0].key.split("_")[0].upper()
        for i, crit in enumerate(kategorie.criteria, start=1):
            quelle = sources.get(crit.key, Source.NOT_COLLECTED.value)
            offen = quelle == Source.NOT_COLLECTED.value
            wert = int(items.get(crit.key, 0) or 0)
            rows.append([
                f"{praefix}-{i:02d}",
                _clean_text(crit.label),
                SOURCE_SHORT.get(quelle, quelle),
                str(crit.max_points),
                "\u2013" if offen else str(wert),
                "nicht erhoben" if offen else _score_status(wert, crit.max_points),
            ])

    return header, rows


def branche_fuer_protokoll(audit_data: dict) -> str:
    """Die Branchenzeile des Auditprotokolls — Befund vor Vermutung.

    Reihenfolge: was das Modell an der Seite erkannt hat, dahinter der Maßstab
    der Klasse; dann die Klasse allein; dann `trade` als Altbestand. `trade`
    stammt bei Widget-Analysen aus einer Stichwortsuche (`scraper.py`) und hat
    einem Ingenieurbüro „Schreiner" ins Protokoll geschrieben, weil „holz" im
    Text stand. Im Protokoll gelesen ist eine Vermutung ein Befund — deshalb
    steht sie hier zuletzt und wird notfalls durch „k.A." ersetzt.
    """
    branche = _clean_text(audit_data.get("erkannte_branche", "") or "").strip()
    klasse = KLASSEN.get(audit_data.get("branchenklasse", "") or "")

    if branche and klasse:
        return f"{branche} ({klasse.bezeichnung})"
    if branche:
        return branche
    if klasse:
        return klasse.bezeichnung

    # `_safe` ersetzt nur None, nicht den leeren Text — hier ist beides gleich
    # unbekannt, und eine leere Protokollzeile sieht aus wie ein Druckfehler.
    return _clean_text(audit_data.get("trade", "") or "").strip() or "k.A."


def generate_audit_report(audit_data: dict) -> bytes:
    """Generate a professional PDF audit report. Returns PDF bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    styles = _get_styles()
    story = []

    total = audit_data.get("total_score", 0) or 0
    level = _clean_text(audit_data.get("level", "Nicht konform") or "Nicht konform")
    company = _clean_text(audit_data.get("company_name", "Unbekannt") or "Unbekannt")
    url = _clean_text(audit_data.get("website_url", "") or "")
    trade = _clean_text(audit_data.get("trade", "") or "")
    city = _clean_text(audit_data.get("city", "") or "")
    created = audit_data.get("created_at", None)
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except (ValueError, TypeError):
            created = datetime.utcnow()
    elif not created:
        created = datetime.utcnow()
    date_str = created.strftime("%d.%m.%Y")
    doc.kc_jahr = created.year  # die Fusszeile datiert sich danach

    items = _parse_json_field(audit_data.get("item_scores")) or {}
    sources = _parse_json_field(audit_data.get("item_sources")) or {}
    categories = _parse_json_field(audit_data.get("category_scores")) or []
    blocker_keys = _parse_json_field(audit_data.get("blockers")) or []
    coverage = audit_data.get("coverage")

    if not isinstance(items, dict) or not items:
        # Ältere Audits haben nur die sechs Altspalten, deren Werte überwiegend
        # geschätzt waren. Ein PDF daraus wäre irreführend.
        raise KatalogFehlt(
            "Dieses Audit stammt aus dem früheren Katalog und enthält keine "
            "Einzelbewertungen. Bitte die Analyse neu ausführen."
        )
    if not isinstance(sources, dict):
        sources = {}

    top_issues = [_clean_text(i) for i in _parse_json_field(audit_data.get("top_issues"))]
    recommendations = [_clean_text(r) for r in _parse_json_field(audit_data.get("recommendations"))]
    ai_summary = _clean_text(audit_data.get("ai_summary", "") or "")

    # ── PAGE 1: COVER ──────────────────────────────────────
    #
    # Die Punktzahl stand hier als <font size="48"> in einem Absatz mit
    # leading=14. Die Glyphen liefen damit aus ihrer Zeilenbox heraus, und das
    # Stufen-Abzeichen darunter zeichnete quer durch die Zahl — auf jedem
    # bisher versendeten PDF war die Bewertung halb verdeckt. Die Zahl bekommt
    # jetzt einen eigenen Stil mit passendem Zeilenabstand.
    story.append(_marken_band(styles))
    story.append(Spacer(1, 26*mm))
    story.append(Paragraph("HOMEPAGE STANDARD", styles["KCTitle"]))
    story.append(Paragraph(
        f"Audit- und Zertifizierungsrahmen {created.year}", styles["KCSubtitle"]))
    story.append(Spacer(1, 18*mm))

    story.append(Paragraph(
        f'{total}<font size="20" color="{KC_TEXT_60.hexval()}"> / 100</font>',
        styles["KCScore"]))
    story.append(Spacer(1, 8*mm))
    story.append(_stufen_abzeichen(level))
    story.append(Spacer(1, 14*mm))

    story.append(Paragraph(f"<b>{company}</b>", styles["KCCenter"]))
    story.append(Paragraph(f'<font color="{KC_TEXT_60.hexval()}">{url}</font>',
                           styles["KCCenter"]))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        f'<font color="{KC_TEXT_60.hexval()}">Auditdatum: {date_str}<br/>'
        f'Auditor: KOMPAGNON Communications</font>', styles["KCCenter"]))

    story.append(PageBreak())

    # ── PAGE 2: LEGAL OVERVIEW ──────────────────────────────
    story.append(Paragraph("Rechtliche Grundlagen", styles["KCHeading"]))
    story.append(Paragraph(
        "Die folgenden Gesetze und Standards bilden die Grundlage f\u00fcr die Bewertung.",
        styles["KCBody"],
    ))

    legal_table = Table(
        rechtstabelle_zellen(),
        colWidths=LEGAL_COL_WIDTHS,
    )
    legal_table.setStyle(_category_table_style(len(LEGAL_ROWS)))
    story.append(legal_table)
    story.append(Spacer(1, 8*mm))

    # BFSG notice box
    bfsg_text = (
        f'<font color="{KC_DARK.hexval()}"><b>Hinweis zum BFSG:</b></font> '
        "Ab dem 28. Juni 2025 gilt das Barrierefreiheitsst\u00e4rkungsgesetz (BFSG) "
        "auch f\u00fcr private Anbieter digitaler Produkte und Dienstleistungen. "
        "Websites m\u00fcssen die WCAG 2.1 Level AA Kriterien erf\u00fcllen."
    )
    bfsg_data = [[Paragraph(bfsg_text, styles["KCBody"])]]
    bfsg_box = Table(bfsg_data, colWidths=[160*mm])
    bfsg_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), KC_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, KC_BORDER),
    ]))
    story.append(bfsg_box)

    story.append(PageBreak())

    # ── PAGE 3: SCORECARD ───────────────────────────────────
    story.append(Paragraph("Bewertungsmatrix", styles["KCHeading"]))

    if blocker_keys:
        blocker_text = "<br/>".join(
            f"\u2022 {_clean_text(BLOCKER_LABELS.get(b, b))}" for b in blocker_keys)
        blocker_box = Table([[Paragraph(
            f'<b>Rechtliche Ausschlusskriterien</b><br/>{blocker_text}<br/>'
            f'<font size="8">Diese Punkte begrenzen die Bewertung unabh\u00e4ngig '
            f'von der erreichten Punktzahl.</font>',
            styles["KCBody"])]], colWidths=[160*mm])
        blocker_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDECEA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBEFORE", (0, 0), (0, -1), 3, KC_DANGER),
        ]))
        story.append(blocker_box)
        story.append(Spacer(1, 5*mm))

    if coverage is not None and coverage < 100:
        story.append(Paragraph(
            # \u202f (schmales gesch. Leerzeichen) fehlt in Helvetica und kam
            # als schwarzes Kaestchen zwischen Zahl und Prozentzeichen heraus.
            # \u00a0 steht in WinAnsi und haelt genauso zusammen.
            f'<font size="8" color="{KC_TEXT_60.hexval()}">{coverage}\u00a0% der Kriterien konnten '
            f'gepr\u00fcft werden. Nicht erhobene Kriterien sind als \u201enicht erhoben\u201c '
            f'ausgewiesen und flie\u00dfen nicht in die Bewertung ein.</font>',
            styles["KCBody"]))
        story.append(Spacer(1, 3*mm))

    sc_header, sc_rows = build_scorecard(items, sources, styles)

    # Summenzeile.
    #
    # Hier stand `level[:15]` in der Statusspalte — aus „Homepage Standard
    # Bronze" wurde „Homepage Standa", abgeschnitten in einer 14 mm breiten
    # Spalte, sodass der Text sichtbar aus der Tabelle lief. Dazu erwischte die
    # Schleife unten diese Zeile als Kategoriekopf und legte ein SPAN ueber die
    # Spalten 0 bis 3, was die Maximalpunkte verschluckte. Die Stufe steht auf
    # dem Deckblatt und auf der letzten Seite; hier gehoert sie nicht hin.
    gesamt_zeile = [
        Paragraph(f'<font color="{KC_WHITE.hexval()}"><b>GESAMTERGEBNIS</b></font>',
                  styles["KCBold"]),
        "", "", "100",
        Paragraph(f'<font color="{KC_WHITE.hexval()}"><b>{total}</b></font>',
                  styles["KCBold"]),
        "",
    ]
    sc_rows.append(gesamt_zeile)

    sc_table = Table(
        [sc_header] + sc_rows,
        # Zusammen 170 mm — die volle Breite zwischen den Raendern. Vorher
        # standen hier 132 mm, also lagen gut 30 mm brach, waehrend „nicht
        # erhoben" rechts aus der Statusspalte lief.
        colWidths=[14*mm, 71*mm, 22*mm, 13*mm, 20*mm, 30*mm],
        repeatRows=1,
    )
    n = len(sc_rows)
    sc_style = list(BASE_TABLE_STYLE)
    for i in range(1, n + 1):
        row_data = sc_rows[i - 1]
        letzte = i == n
        # Kategoriekopf — erkennbar am Paragraph in der ersten Spalte. Die
        # Summenzeile sieht genauso aus und muss ausgenommen werden.
        if isinstance(row_data[0], Paragraph) and not letzte:
            sc_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(brand.INFO_BG)))
            sc_style.append(("SPAN", (0, i), (3, i)))
        elif not letzte and i % 2 == 0:
            sc_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
        if isinstance(row_data[-1], str) and row_data[-1] in STATUS_ZEICHEN.values():
            sc_style.append(("TEXTCOLOR", (-1, i), (-1, i), _status_color(row_data[-1])))
            sc_style.append(("FONTNAME", (-1, i), (-1, i), FONT_BOLD))
            sc_style.append(("ALIGN", (-1, i), (-1, i), "CENTER"))

    sc_style.append(("BACKGROUND", (0, n), (-1, n), KC_DARK))
    sc_style.append(("TEXTCOLOR", (0, n), (-1, n), KC_WHITE))
    sc_style.append(("SPAN", (0, n), (2, n)))
    sc_table.setStyle(TableStyle(sc_style))
    story.append(sc_table)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f'Legende: <font color="{KC_SUCCESS.hexval()}"><b>{STATUS_ZEICHEN["konform"]}</b></font> konform '
        f'&nbsp;·&nbsp; <font color="{KC_WARNING.hexval()}"><b>{STATUS_ZEICHEN["teilweise"]}</b></font> teilweise konform '
        f'&nbsp;·&nbsp; <font color="{KC_DANGER.hexval()}"><b>{STATUS_ZEICHEN["offen"]}</b></font> nicht konform '
        f'&nbsp;·&nbsp; „nicht erhoben" fließt nicht in die Bewertung ein',
        styles["KCSmall"],
    ))

    story.append(PageBreak())

    # ── PAGE 4: AUDIT PROTOCOL ──────────────────────────────
    story.append(Paragraph("Auditprotokoll", styles["KCHeading"]))

    proto_data = [
        ["Website-URL", url],
        ["Auftraggeber / Unternehmen", company],
        ["Branche", branche_fuer_protokoll(audit_data)],
        ["Stadt", _safe(city, "k.A.")],
        ["Auditdatum", date_str],
        ["Auditor/in", "KOMPAGNON Communications"],
        ["Audittyp", "Erst-Audit"],
    ]
    proto_table = Table(proto_data, colWidths=[50*mm, 110*mm])
    proto_table.setStyle(TableStyle(_stil_ohne_kopfzeile(len(proto_data))))
    story.append(proto_table)
    story.append(Spacer(1, 8*mm))

    # Hosting analysis
    story.append(Paragraph("Technische Pr\u00fcfergebnisse", styles["KCHeading"]))
    ssl_ok = audit_data.get("ssl_ok", False)
    mobile = audit_data.get("mobile_score", 0) or 0
    lcp = audit_data.get("lcp_value")
    cls_val = audit_data.get("cls_value")

    tech_data = [
        ["Pr\u00fcfung", "Ergebnis"],
        ["SSL-Zertifikat", "Vorhanden" if ssl_ok else "Nicht vorhanden"],
        ["HTTPS aktiv", "Ja" if ssl_ok else "Nein"],
        ["Mobile-Score", f"{mobile} / 100"],
        ["LCP", f"{lcp:.1f}s" if lcp else "k.A."],
        ["CLS", f"{cls_val:.3f}" if cls_val else "k.A."],
    ]
    tech_table = Table(tech_data, colWidths=[50*mm, 110*mm])
    tech_table.setStyle(_category_table_style(len(tech_data) - 1))
    story.append(tech_table)
    story.append(Spacer(1, 8*mm))

    # Score summary
    story.append(Paragraph("Pr\u00fcfergebnis je Kategorie", styles["KCHeading"]))
    sum_data = [["Kategorie", "Ergebnis"]]
    for kategorie in categories:
        beschriftung = f"{kategorie.get('label', '')} (max. {kategorie.get('nominal_max', 0)})"
        if kategorie.get("max", 0) < kategorie.get("nominal_max", 0):
            beschriftung += " – teilweise prüfbar"
        sum_data.append([_clean_text(beschriftung),
                         f"{kategorie.get('score', 0)} / {kategorie.get('max', 0)}"])
    sum_data.append(["GESAMTERGEBNIS (normiert)", f"{total} / 100"])

    sum_table = Table(sum_data, colWidths=[110*mm, 50*mm])
    sum_style = list(BASE_TABLE_STYLE)
    sum_style.append(("ALIGN", (1, 0), (1, -1), "RIGHT"))
    sum_style.append(("BACKGROUND", (0, -1), (-1, -1), KC_DARK))
    sum_style.append(("TEXTCOLOR", (0, -1), (-1, -1), KC_WHITE))
    for i in range(1, len(sum_data) - 1):
        if i % 2 == 0:
            sum_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
    sum_table.setStyle(TableStyle(sum_style))
    story.append(sum_table)
    story.append(Spacer(1, 8*mm))

    # ── CHARTS: Radar + Donut ───────────────────────────────
    try:
        radar_axes = [
            (_clean_text(k.get("label", "")).split(" &")[0],
             round((k.get("score", 0) / k["max"]) * 10, 1) if k.get("max") else 0)
            for k in categories
        ]
        keyword_positions = audit_data.get("keyword_positions") or {}
        if isinstance(keyword_positions, str):
            try:
                keyword_positions = json.loads(keyword_positions)
            except Exception:
                keyword_positions = {}

        caption_style = ParagraphStyle(
            "ChartCaption", fontName=FONT_NORMAL, fontSize=8,
            textColor=KC_TEXT_60, alignment=TA_CENTER,
        )

        # Der Ring kommt nur, wenn es Keyword-Daten gibt. Fehlten sie, zeichnete
        # er vier gleiche Viertel mit „25 %" — eine erfundene Verteilung, die
        # der Empfaenger als Messergebnis liest.
        donut_png = generate_donut_chart(keyword_positions)

        if donut_png:
            chart_w = 72 * mm
            chart_table = Table(
                [[RLImage(BytesIO(generate_radar_chart(radar_axes)),
                          width=chart_w, height=chart_w),
                  RLImage(BytesIO(donut_png), width=chart_w, height=chart_w)],
                 [Paragraph("Zielerreichung je Bereich", caption_style),
                  Paragraph("Keyword-Positionen", caption_style)]],
                colWidths=[chart_w + 4*mm, chart_w + 4*mm],
            )
        else:
            # Ohne zweites Diagramm stand das Radar klein und links angeschlagen
            # neben einer halbleeren Seite. Allein darf es groesser und mittig.
            chart_w = 105 * mm
            chart_table = Table(
                [[RLImage(BytesIO(generate_radar_chart(radar_axes)),
                          width=chart_w, height=chart_w)],
                 [Paragraph("Zielerreichung je Bereich", caption_style)],
                 [Paragraph(
                     "Keyword-Positionen werden in dieser Analyse nicht erhoben.",
                     caption_style)]],
                colWidths=[chart_w + 8*mm],
            )
        chart_table.hAlign = "CENTER"
        chart_table.setStyle(TableStyle([
            ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table)
    except Exception as chart_fehler:  # noqa: BLE001
        # Diagramme sind Beiwerk und duerfen das PDF nicht kippen — aber
        # lautlos verschwinden sollen sie auch nicht.
        logger.warning(f"Diagramme nicht erzeugt: {chart_fehler}")

    story.append(PageBreak())

    # ── PAGE 5: ISSUES & RECOMMENDATIONS ────────────────────
    story.append(Paragraph("Ma\u00dfnahmen & Empfehlungen", styles["KCHeading"]))

    if top_issues:
        story.append(Paragraph(f'<font color="{KC_DANGER.hexval()}"><b>Kritische M\u00e4ngel</b></font>', styles["KCBody"]))
        issue_rows = [["Nr.", "Mangel"]]
        for i, issue in enumerate(top_issues, 1):
            issue_rows.append([str(i), Paragraph(str(issue), styles["KCBody"])])
        issue_table = Table(issue_rows, colWidths=[12*mm, 148*mm])
        issue_style = list(BASE_TABLE_STYLE)
        issue_style[1] = ("FONTSIZE", (0, 0), (-1, 0), 9)
        issue_style.append(("BACKGROUND", (0, 0), (-1, 0), KC_DANGER))
        issue_table.setStyle(TableStyle(issue_style))
        story.append(issue_table)
        story.append(Spacer(1, 6*mm))

    if recommendations:
        story.append(Paragraph(f'<font color="{KC_SUCCESS.hexval()}"><b>Empfehlungen</b></font>', styles["KCBody"]))
        rec_rows = [["Prio.", "Ma\u00dfnahme"]]
        prio_labels = ["hoch", "hoch", "mittel", "mittel", "niedrig"]
        for i, rec in enumerate(recommendations):
            prio = prio_labels[i] if i < len(prio_labels) else "niedrig"
            rec_rows.append([prio, Paragraph(str(rec), styles["KCBody"])])
        rec_table = Table(rec_rows, colWidths=[18*mm, 142*mm])
        rec_style = list(BASE_TABLE_STYLE)
        rec_style.append(("BACKGROUND", (0, 0), (-1, 0), KC_SUCCESS))
        rec_table.setStyle(TableStyle(rec_style))
        story.append(rec_table)
        story.append(Spacer(1, 6*mm))

    if ai_summary:
        story.append(Paragraph("Bewertung durch KOMPAGNON", styles["KCHeading"]))
        ai_box = [[Paragraph(ai_summary, styles["KCBody"])]]
        ai_table = Table(ai_box, colWidths=[160*mm])
        ai_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), KC_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, KC_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(ai_table)

    story.append(PageBreak())

    # ── PAGE 6: GEO & KI-SICHTBARKEIT ───────────────────────
    story.append(Paragraph("GEO \u0026 KI-Sichtbarkeit", styles["KCHeading"]))
    story.append(Paragraph(
        "KI-Suchsysteme wie ChatGPT, Google AI Overview oder Perplexity crawlen Websites "
        "nach eigenen Regeln. Die folgenden Prüfpunkte zeigen, wie gut die Website für "
        "diese neuen Sichtbarkeitskanäle aufgestellt ist.",
        styles["KCBody"],
    ))
    story.append(Spacer(1, 4*mm))

    # Farben wie in der Bewertungsmatrix, damit derselbe Status gleich
    # aussieht. Wortstatus statt Haekchen: Helvetica kennt ✓ und ✗ nicht,
    # die Spalte blieb dadurch in jedem bisherigen Bericht leer.
    STATUS_FARBEN = {
        STATUS_ERFUELLT: "#27ae60",
        STATUS_OFFEN: "#e74c3c",
        STATUS_UNBEKANNT: KC_TEXT_60.hexval(),
    }

    def _geo_status_zelle(status):
        return Paragraph(
            f'<font color="{STATUS_FARBEN[status]}"><b>{status}</b></font>',
            ParagraphStyle("GeoStatus", fontName=FONT_BOLD, fontSize=9,
                           leading=11, alignment=TA_CENTER),
        )

    geo_header = ["Prüfpunkt", "Status", "Empfehlung"]
    geo_rows = [
        [
            punkt["pruefpunkt"],
            _geo_status_zelle(punkt["status"]),
            Paragraph(_clean_text(punkt["empfehlung"]), styles["KCZelle"])
            if punkt["empfehlung"]
            else Paragraph(
                f'<font color="{KC_TEXT_60.hexval()}">'
                f'{_clean_text(punkt["hinweis"])}</font>', styles["KCZelle"]),
        ]
        for punkt in geo_pruefpunkte(audit_data)
    ]

    geo_table = Table(
        [geo_header] + geo_rows,
        colWidths=[55*mm, 30*mm, 75*mm],
    )
    geo_style = list(BASE_TABLE_STYLE)
    for i in range(1, len(geo_rows) + 1):
        if i % 2 == 0:
            geo_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
        geo_style.append(("ALIGN", (1, i), (1, i), "CENTER"))
        geo_style.append(("VALIGN", (1, i), (1, i), "MIDDLE"))
    geo_table.setStyle(TableStyle(geo_style))
    story.append(geo_table)
    story.append(Spacer(1, 6*mm))

    # GEO info box
    geo_info = (
        '<b>Was ist llms.txt?</b> Eine neue Konvention (ähnlich robots.txt) die KI-Systemen '
        'mitteilt, welche Inhalte für das Training oder die Antwortgenerierung genutzt werden '
        'dürfen. Websites mit llms.txt werden von ChatGPT, Claude \u0026 Co. bevorzugt zitiert.'
    )
    geo_box = Table([[Paragraph(geo_info, styles["KCBody"])]], colWidths=[160*mm])
    geo_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(brand.INFO_BG)),
        ("BOX", (0, 0), (-1, -1), 0.5, KC_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(geo_box)

    story.append(PageBreak())

    # ── PAGE 7: MASSNAHMEN-ROADMAP ───────────────────────────
    story.append(Paragraph("Ma\u00dfnahmen-Roadmap", styles["KCHeading"]))
    story.append(Paragraph(
        "Basierend auf den Audit-Ergebnissen empfehlen wir folgende Umsetzungsreihenfolge:",
        styles["KCBody"],
    ))
    story.append(Spacer(1, 6*mm))

    # Die Massnahmen kommen aus dem Befund statt aus einer festen Liste:
    # `roadmap_massnahmen` nennt nur, was gemessen wurde und offen ist. Vorher
    # stand "robots.txt: GPTBot-Blockierung entfernen" in jedem Bericht, auch
    # fuer eine robots.txt, die niemanden sperrt.
    massnahmen = roadmap_massnahmen(audit_data)

    quick_wins = list(massnahmen["sofort"])
    mobile_ps = audit_data.get("mobile_score") or 0
    if mobile_ps and mobile_ps < 50:
        quick_wins.append("Bilder komprimieren \u0026 Lazy Load aktivieren")
    if not quick_wins:
        quick_wins.append("Audit-Score weiter optimieren \u0026 Inhalte aktualisieren")

    midterm = list(massnahmen["mittelfristig"])
    if level == "Nicht konform":
        midterm.append("SSL, Datenschutzerkl\u00e4rung und Impressum pr\u00fcfen \u0026 korrigieren")

    longterm = list(massnahmen["langfristig"])

    def _roadmap_box(title, items, bg_color, border_color, phase_label):
        """Build a single phase box as a Table."""
        header_para = Paragraph(
            f'<font color="white"><b>{phase_label} — {title}</b></font>',
            ParagraphStyle("RoadmapHeader", fontName=FONT_BOLD, fontSize=11,
                           textColor=KC_WHITE, alignment=TA_LEFT),
        )
        header_row = Table([[header_para]], colWidths=[160*mm])
        header_row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(border_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        item_rows = []
        for item in items:
            item_rows.append([
                Paragraph(f"\u2022 {_clean_text(item)}", styles["KCBody"]),
            ])
        body = Table(item_rows, colWidths=[160*mm])
        body.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(border_color)),
        ]))
        return KeepTogether([header_row, body])

    story.append(_roadmap_box(
        "Quick Wins (Woche 1\u20132)", quick_wins,
        bg_color=brand.SUCCESS_BG, border_color=brand.SUCCESS, phase_label="Phase 1",
    ))
    story.append(Spacer(1, 5*mm))
    story.append(_roadmap_box(
        "Mittelfristig (Monat 1\u20133)", midterm,
        bg_color=brand.INFO_BG, border_color=brand.MID, phase_label="Phase 2",
    ))
    story.append(Spacer(1, 5*mm))
    story.append(_roadmap_box(
        "Langfristig (Monat 3\u20136)", longterm,
        bg_color=brand.SURFACE, border_color=brand.DARK, phase_label="Phase 3",
    ))

    story.append(PageBreak())

    # ── LAST PAGE: CERTIFICATION ────────────────────────────
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Zertifizierungsaussage", styles["KCTitle"]))
    story.append(Spacer(1, 10*mm))

    story.append(_stufen_abzeichen(level))
    story.append(Spacer(1, 10*mm))

    cert_text = (
        f"Hiermit wird best\u00e4tigt, dass die gepr\u00fcfte Website "
        f"<b>{url}</b> zum Zeitpunkt des Audits am <b>{date_str}</b> "
        f"den Anforderungen des <b>{level}</b> "
        f"entspricht und eine Gesamtbewertung von <b>{total} / 100 Punkten</b> "
        f"erzielt hat."
    )
    story.append(Paragraph(cert_text, styles["KCBody"]))
    story.append(Spacer(1, 20*mm))

    # Signature lines
    sig_data = [["Ort, Datum", "Auditor/in: KOMPAGNON", "Auftraggeber"]]
    sig_table = Table(sig_data, colWidths=[53*mm, 54*mm, 53*mm])
    sig_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, KC_DARK),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NORMAL),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    story.append(sig_table)

    # Build PDF
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
