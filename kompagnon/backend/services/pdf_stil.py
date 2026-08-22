"""Farben, Schriften, Absatzformate — das Fundament der PDFs (L-25).

**Warum eigene Datei, 22.08.2026.** `services/pdf_generator.py` hatte 1.424
Zeilen — davon **575 in einer einzigen Funktion**, `generate_audit_report`.
Alles, was jede PDF-Seite braucht und niemand einzeln aendert: die
Markenfarben, der Schriftordner, der Zeichenvorrat und die Absatzformate.
"""
import os
import unicodedata
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from services import brand
import logging


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


logger = logging.getLogger(__name__)


KC_DARK = colors.HexColor(brand.DARK)


KC_TEXT = colors.HexColor(brand.TEXT)


KC_TEXT_60 = colors.HexColor(brand.TEXT_60)


KC_WHITE = colors.white


KC_BORDER = colors.HexColor(brand.BORDER)


KC_DANGER = colors.HexColor(brand.ERROR)


KC_LIGHT = colors.HexColor(brand.SURFACE)


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


ZEICHENVORRAT = _unterstuetzte_zeichen()


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


# Einmal beim Laden registrieren; beide Namen brauchen alle vier Dateien.
FONT_NORMAL, FONT_BOLD = _register_fonts()


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
