"""
Briefing PDF Export — Website-Briefing für Kunden.
3 Seiten: Deckblatt | Inhalte | Nächste Schritte
"""
import unicodedata
import os
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Brand ────────────────────────────────────────────────────────────────────
TEAL       = colors.HexColor("#008EAA")
DARK_TEAL  = colors.HexColor("#004F59")
LIGHT_GREY = colors.HexColor("#F4F7F8")
MID_GREY   = colors.HexColor("#8A9BA8")
TEXT_DARK  = colors.HexColor("#1A2C32")
WHITE      = colors.white
FOOTER_TXT = "KOMPAGNON Communications BP GmbH · kompagnon.eu"

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


# ── Font ─────────────────────────────────────────────────────────────────────
def _register_fonts():
    try:
        import reportlab
        fp = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        pdfmetrics.registerFont(TTFont("DV",     os.path.join(fp, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DV-Bold", os.path.join(fp, "DejaVuSans-Bold.ttf")))
        return "DV", "DV-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"

FONT, FONT_B = _register_fonts()


def _t(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text))


# ── Footer/Header callback ────────────────────────────────────────────────────
def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 7)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(MARGIN, 10 * mm, FOOTER_TXT)
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Seite {doc.page}")
    canvas.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    return {
        "cover_brand": ParagraphStyle("cover_brand",
            fontName=FONT_B, fontSize=32, textColor=TEAL,
            alignment=TA_CENTER, spaceAfter=6),
        "cover_title": ParagraphStyle("cover_title",
            fontName=FONT_B, fontSize=22, textColor=TEXT_DARK,
            alignment=TA_CENTER, spaceAfter=4),
        "cover_company": ParagraphStyle("cover_company",
            fontName=FONT_B, fontSize=16, textColor=DARK_TEAL,
            alignment=TA_CENTER, spaceAfter=4),
        "cover_sub": ParagraphStyle("cover_sub",
            fontName=FONT, fontSize=10, textColor=MID_GREY,
            alignment=TA_CENTER, spaceAfter=2),
        "section_head": ParagraphStyle("section_head",
            fontName=FONT_B, fontSize=11, textColor=WHITE,
            spaceAfter=0, spaceBefore=0, leftIndent=4),
        "field_label": ParagraphStyle("field_label",
            fontName=FONT_B, fontSize=8, textColor=MID_GREY,
            spaceAfter=1, spaceBefore=6),
        "field_value": ParagraphStyle("field_value",
            fontName=FONT, fontSize=9, textColor=TEXT_DARK,
            spaceAfter=2, leading=13),
        "step_num": ParagraphStyle("step_num",
            fontName=FONT_B, fontSize=18, textColor=TEAL,
            alignment=TA_CENTER),
        "step_text": ParagraphStyle("step_text",
            fontName=FONT_B, fontSize=11, textColor=TEXT_DARK,
            spaceAfter=4),
        "step_sub": ParagraphStyle("step_sub",
            fontName=FONT, fontSize=9, textColor=MID_GREY,
            spaceAfter=8),
        "normal": ParagraphStyle("normal",
            fontName=FONT, fontSize=9, textColor=TEXT_DARK, leading=13),
    }


# ── Section helper ────────────────────────────────────────────────────────────
def _section(title, rows, S):
    """Render a labelled section block with a teal header bar."""
    elems = []
    # Header bar
    header = Table(
        [[Paragraph(_t(title), S["section_head"])]],
        colWidths=[(PAGE_W - 2 * MARGIN)],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    elems.append(header)
    elems.append(Spacer(1, 3 * mm))
    for label, value in rows:
        elems.append(Paragraph(_t(label), S["field_label"]))
        display = _t(value) if value else "–"
        elems.append(Paragraph(display, S["field_value"]))
    elems.append(Spacer(1, 4 * mm))
    return elems


# ── Main generator ────────────────────────────────────────────────────────────
def generate_briefing_pdf(briefing, company_name: str) -> bytes:
    """
    Generate a 3-page briefing PDF.
    briefing: ORM Briefing object (or dict-like).
    company_name: Lead company name string.
    Returns bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=20 * mm,
        title=f"Website-Briefing – {company_name}",
        author="KOMPAGNON",
    )
    S = _styles()
    story = []

    # ── PAGE 1: Cover ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("KOMPAGNON", S["cover_brand"]))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="60%", thickness=2, color=TEAL, hAlign="CENTER"))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Website-Briefing", S["cover_title"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(_t(company_name), S["cover_company"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        datetime.now().strftime("%d. %B %Y"),
        S["cover_sub"],
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="60%", thickness=1, color=LIGHT_GREY, hAlign="CENTER"))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Vertraulich – erstellt im Strategy Workshop",
        S["cover_sub"],
    ))
    story.append(PageBreak())

    # ── PAGE 2: Contents ──────────────────────────────────────────────────────
    def _b(field):
        val = getattr(briefing, field, None)
        if isinstance(val, bool):
            return "Ja" if val else "Nein"
        return val or ""

    # Build two columns using a Table
    col_w = (PAGE_W - 2 * MARGIN - 6 * mm) / 2

    def _col_section(title, rows):
        elems = []
        # Teal header
        hdr = Table([[Paragraph(_t(title), S["section_head"])]], colWidths=[col_w])
        hdr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), TEAL),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ]))
        elems.append(hdr)
        elems.append(Spacer(1, 2 * mm))
        for label, value in rows:
            elems.append(Paragraph(_t(label), S["field_label"]))
            display = _t(value) if value else "–"
            elems.append(Paragraph(display, S["field_value"]))
        elems.append(Spacer(1, 4 * mm))
        return elems

    left = (
        _col_section("Betrieb & Leistungen", [
            ("Gewerk / Branche", _b("gewerk")),
            ("Leistungen",       _b("leistungen")),
            ("Einzugsgebiet",    _b("einzugsgebiet")),
        ])
        + _col_section("Design & Wünsche", [
            ("Farbwünsche",  _b("farben")),
            ("Stil",         _b("stil")),
            ("Vorbilder",    _b("vorbilder")),
        ])
    )

    right = (
        _col_section("Zielgruppe & Positionierung", [
            ("Zielgruppe",   _b("zielgruppe") if not isinstance(getattr(briefing, "zielgruppe", None), str)
                             else _b("zielgruppe")),
            ("USP",          _b("usp")),
            ("Mitbewerber",  _b("mitbewerber")),
        ])
        + _col_section("Seiten & Assets", [
            ("Gewünschte Seiten", _b("wunschseiten")),
            ("Logo vorhanden",    "Ja" if getattr(briefing, "logo_vorhanden", False) else "Nein"),
            ("Fotos vorhanden",   "Ja" if getattr(briefing, "fotos_vorhanden", False) else "Nein"),
            ("Sonstige Hinweise", _b("sonstige_hinweise")),
        ])
    )

    # Pad to equal length
    max_len = max(len(left), len(right))
    while len(left)  < max_len: left.append(Spacer(1, 1))
    while len(right) < max_len: right.append(Spacer(1, 1))

    two_col = Table(
        [[left, right]],
        colWidths=[col_w, col_w],
        hAlign="LEFT",
    )
    two_col.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 0),
        ("TOPPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0,0), (-1, -1), 0),
        ("INNERGRID",   (0, 0), (-1, -1), 0, WHITE),
        ("COLPADDING",  (0, 0), (0, -1), 0),
    ]))
    # Wrap columns with gutter
    outer = Table([[left, Spacer(6 * mm, 1), right]], colWidths=[col_w, 6 * mm, col_w])
    outer.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(outer)
    story.append(PageBreak())

    # ── PAGE 3: Next Steps ────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Nächste Schritte", S["cover_title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL))
    story.append(Spacer(1, 8 * mm))

    steps = [
        ("1", "Phase 1: Sitemap & Struktur festlegen",
         "Gemeinsam definieren wir die Seitenstruktur und den Navigationsaufbau Ihrer neuen Website."),
        ("2", "Phase 2: KI-Textentwurf generieren und abstimmen",
         "Auf Basis des Briefings erstellen wir mit KI-Unterstützung erste Textvorschläge für alle Seiten."),
        ("3", "Phase 3: Design-Mockup präsentieren und freigeben",
         "Sie erhalten ein visuelles Mockup und erteilen nach Abstimmung die Freigabe für die Umsetzung."),
        ("4", "Phase 4: Go-Live",
         "Nach finaler Qualitätsprüfung geht Ihre neue Website live – inkl. Einweisung und Übergabe."),
    ]

    for num, title, sub in steps:
        row = Table(
            [[Paragraph(num, S["step_num"]),
              [Paragraph(_t(title), S["step_text"]),
               Paragraph(_t(sub),   S["step_sub"])]]],
            colWidths=[14 * mm, PAGE_W - 2 * MARGIN - 14 * mm],
        )
        row.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
            ("BACKGROUND",   (0, 0), (0, -1), LIGHT_GREY),
            ("ROUNDEDCORNERS", [3]),
        ]))
        story.append(KeepTogether(row))
        story.append(Spacer(1, 5 * mm))

    # Build PDF
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
