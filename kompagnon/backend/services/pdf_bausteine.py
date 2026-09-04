"""Die Bauteile des Auditberichts — Farben, Stile, Tabellenhelfer.

Am 2026-08-30 aus `pdf_generator.py` herausgeloest (L-25). Die Datei trug 905
Zeilen und darin zwei Dinge: **womit** ein Bericht gebaut wird und **wie** er
gebaut wird. Hier steht das Erste.

Wer eine Farbe, einen Tabellenstil oder die Fusszeile sucht, sucht hier. Wer
wissen will, was auf Seite 4 steht, sucht in `pdf_bericht_seiten.py`.

**Die Farben kommen aus `services/brand.py`**, dem Gegenstueck zu `tokens.css`.
Hier stand einmal eine vierte, voellig eigene Palette (#2c3e50, #f39c12,
#e74c3c — Flat-UI-Toene); Widget, Mail, Berichtsseite und PDF sahen damit nach
vier verschiedenen Absendern aus. `test_pdf_report` prueft, dass keine davon
zurueckkommt — **in dieser Datei und in ihren zwei Geschwistern**.
"""
import json
from services.pdf_stil import BASE_TABLE_STYLE, FONT_BOLD, FONT_NORMAL, KC_BORDER, KC_DANGER, KC_DARK, KC_LIGHT, KC_TEXT_60, KC_WHITE, _clean_text, _get_styles, _register_fonts, _stil_ohne_kopfzeile
from services.pdf_kataloge import KatalogFehlt, LEGAL_COL_WIDTHS, LEGAL_ROWS, STATUS_ERFUELLT, STATUS_OFFEN, STATUS_UNBEKANNT, geo_pruefpunkte, rechtstabelle_zellen, roadmap_massnahmen
from services.pdf_diagramme import _stufen_abzeichen, generate_donut_chart, generate_radar_chart
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




# ═══════════════════════════════════════════════════════════
# Schriftregistrierung
# ═══════════════════════════════════════════════════════════














# ═══════════════════════════════════════════════════════════
# Colors
# ═══════════════════════════════════════════════════════════

# Die Werte kommen aus services/brand.py, dem Gegenstueck zu tokens.css.
# Hier stand eine vierte, voellig eigene Palette (#2c3e50, #f39c12, #e74c3c —
# Flat-UI-Toene). Widget, Mail, Berichtsseite und PDF sahen damit nach vier
# verschiedenen Absendern aus.
from services import brand  # noqa: E402

KC_MID = colors.HexColor(brand.MID)
KC_YELLOW = colors.HexColor(brand.YELLOW)
KC_SUCCESS = colors.HexColor(brand.SUCCESS)
KC_WARNING = colors.HexColor(brand.WARN)
KC_ROT = KC_DANGER
KC_ERROR_BG = colors.HexColor(brand.ERROR_BG)


# ═══════════════════════════════════════════════════════════
# Styles
# ═══════════════════════════════════════════════════════════



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



def radar_beschriftung(label: str) -> str:
    """Der Name einer Kategorie ohne ihren Zusatz — fuer die Achsen des Radars.

    Gekuerzt wurde vorher mit ``split(" &")[0]``. Das traf sieben der acht
    Kategorien; „Barrierefreiheit (WCAG/BFSG)" fuehrt kein „&" und stand als
    einzige in voller Laenge am Rand der Grafik. Getrennt wird deshalb am
    ersten Zusatz, gleich ob er mit „&", einer Klammer oder einem Schraegstrich
    beginnt.
    """
    name = (label or "").strip()
    for trenner in (" &", " (", " /", " –", " —"):
        name = name.split(trenner)[0]
    return name.strip()






# ═══════════════════════════════════════════════════════════
# Main generator
# ═══════════════════════════════════════════════════════════

def build_scorecard(items: dict, sources: dict, styles: dict,
                    belege: dict = None) -> tuple:
    """Bewertungsmatrix: Kopfzeile je Kategorie plus eine Zeile je Kriterium.

    Die Zeilenwerte stammen aus der Einzelbewertung. Früher wurde der
    Kategorie-Score proportional auf die Kriterien verteilt — die Zahlen pro
    Zeile waren also gerechnet, nicht gemessen.

    Nicht erhobene Kriterien erscheinen mit Gedankenstrich und zählen weder
    in den erreichten noch in den möglichen Punkten der Kategorie.
    """
    header = ["ID", "Pr\u00fcfbereich", "Quelle", "Max.", "Ist", "Status"]
    rows = []
    belege = belege or {}

    for kategorie in CATALOGUE:
        erhoben = [c for c in kategorie.criteria
                   if sources.get(c.key, Source.NOT_COLLECTED.value)
                   != Source.NOT_COLLECTED.value]
        erreicht = sum(int(items.get(c.key, 0) or 0) for c in erhoben)
        moeglich = sum(c.max_points for c in erhoben)

        kopf = f"{kategorie.label} (max. {kategorie.max_points} Pkt.)"
        if moeglich < kategorie.max_points:
            # **Nicht nur die Punkte, auch die Zahl der Kriterien (L-151).**
            # „0 / 2" allein liest sich als Urteil ueber den Betrieb; dass
            # davon vier von fuenf Kriterien gar nicht erhoben werden konnten,
            # stand nur in den Einzelzeilen — und die Ueberschrift liest man
            # zuerst.
            kopf += (f" \u2013 {len(erhoben)} von {len(kategorie.criteria)} "
                     f"Kriterien pr\u00fcfbar, {moeglich} Pkt.")

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
            beleg = "" if offen else _clean_text(belege.get(crit.key, "") or "")
            bereich = _clean_text(crit.label)
            if beleg:
                bereich = Paragraph(
                    f'{_clean_text(crit.label)}<br/>'
                    f'<font size="7" color="#4A5A5C">{beleg}</font>',
                    styles["KCSmall"] if "KCSmall" in styles else styles["KCBody"])
            rows.append([
                f"{praefix}-{i:02d}",
                bereich,
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


