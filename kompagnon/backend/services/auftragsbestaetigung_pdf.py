"""
Auftragsbestätigung PDF Generator — KOMPAGNON Communications BP GmbH
Erstellt eine professionelle Auftragsbestätigung als PDF-Bytes via ReportLab.
"""
import os
import unicodedata
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _register_fonts():
    try:
        import reportlab
        font_path = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(font_path, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(font_path, "DejaVuSans-Bold.ttf")))
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _clean_text(text):
    """Normalize Unicode text for PDF rendering."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize("NFC", text)


PAKETE = {
    "starter": {
        "name":    "Starter-Paket",
        "netto":   1260.50,
        "brutto":  1500.00,
        "leistungen": [
            "5-seitige WordPress-Website",
            "Mobile-First Design (responsiv)",
            "SEO-Grundoptimierung",
            "SSL-Zertifikat & DSGVO-konform",
            "Kontaktformular",
            "30 Tage kostenloser Support",
            "Lieferzeit: 7-10 Werktage",
        ],
    },
    "kompagnon": {
        "name":    "KOMPAGNON-Paket",
        "netto":   1680.67,
        "brutto":  2000.00,
        "leistungen": [
            "8-seitige WordPress-Website",
            "Mobile-First Design (responsiv)",
            "SEO + GEO-Optimierung (lokale Suche)",
            "Strategy Workshop (60 Min.)",
            "Schema Markup & KI-Optimierung",
            "SSL-Zertifikat & DSGVO-konform",
            "Kontakt- und Anfrageformulare",
            "Google Business Profil-Verknuepfung",
            "30 Tage kostenloser Support",
            "Lieferzeit: 14 Werktage",
        ],
    },
    "premium": {
        "name":    "Premium-Paket",
        "netto":   2352.94,
        "brutto":  2800.00,
        "leistungen": [
            "12-seitige WordPress-Website",
            "Individual-Design nach CI",
            "SEO + GEO + KI-Volloptimierung",
            "Strategy Workshop (90 Min.)",
            "Professioneller Fotoshooting-Tag",
            "Shop-Funktionalitaet (WooCommerce)",
            "SSL-Zertifikat & DSGVO-konform",
            "Alle Formulare & Integrationen",
            "Google Ads Einrichtung",
            "3 Monate kostenloser Support",
            "Lieferzeit: 21 Werktage",
        ],
    },
}


def generate_auftragsbestaetigung(
    session_id: str,
    customer_name: str,
    customer_email: str,
    company_name: str,
    package_id: str,
    amount_eur: float,
    datum: str,
) -> bytes:
    """Erstellt eine Auftragsbestätigung als PDF-Bytes."""

    paket = PAKETE.get(package_id, PAKETE["kompagnon"])
    mwst  = round(paket["brutto"] - paket["netto"], 2)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20*mm, bottomMargin=25*mm,
        leftMargin=25*mm, rightMargin=25*mm,
    )

    fn, fb = _register_fonts()

    KC_TEAL   = colors.HexColor("#008eaa")
    KC_DARK   = colors.HexColor("#1a2332")
    KC_GRAY   = colors.HexColor("#64748b")
    KC_LIGHT  = colors.HexColor("#f8f9fa")
    KC_GREEN  = colors.HexColor("#1D9E75")
    KC_WHITE  = colors.white
    KC_BORDER = colors.HexColor("#e2e8f0")

    def ps(name, **kw):
        return ParagraphStyle(name, fontName=fn, textColor=KC_DARK, **kw)

    st_label   = ps("label",   fontSize=8,  fontName=fb, textColor=KC_GRAY,
                    spaceAfter=2, leading=10)
    st_value   = ps("value",   fontSize=10, spaceAfter=2, leading=13)
    st_section = ps("section", fontSize=11, fontName=fb, textColor=KC_TEAL,
                    spaceAfter=4, spaceBefore=8)
    st_item    = ps("item",    fontSize=9,  textColor=KC_GRAY, leading=14)
    st_right   = ps("right",   fontSize=9,  alignment=TA_RIGHT)

    def footer_cb(canvas_obj, doc_ref):
        canvas_obj.saveState()
        canvas_obj.setFont(fn, 7)
        canvas_obj.setFillColor(KC_GRAY)
        w, _ = A4
        canvas_obj.drawString(
            25*mm, 12*mm,
            _clean_text(
                "KOMPAGNON Communications BP GmbH  |  "
                "kompagnon.eu  |  info@kompagnon.eu"
            )
        )
        canvas_obj.drawRightString(
            w - 25*mm, 12*mm,
            _clean_text(f"Seite {doc_ref.page}")
        )
        canvas_obj.restoreState()

    story = []

    # ── HEADER-BALKEN ─────────────────────────────────────
    header_data = [[
        Paragraph(
            '<font color="white"><b>KOMPAGNON</b></font>',
            ParagraphStyle("hd", fontName=fb, fontSize=20, textColor=KC_WHITE)
        ),
        Paragraph(
            '<font color="white">Auftragsbestaetigung</font>',
            ParagraphStyle("hd2", fontName=fn, fontSize=11,
                           textColor=KC_WHITE, alignment=TA_RIGHT)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[90*mm, 75*mm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), KC_TEAL),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 8*mm))

    # ── RECHNUNGS-METADATEN ───────────────────────────────
    short_id = (session_id[:24] + "...") if len(session_id) > 24 else session_id
    meta_data = [
        [
            Paragraph(_clean_text("AUFTRAGGEBER"),  st_label),
            Paragraph(_clean_text("BESTELLNUMMER"), st_label),
        ],
        [
            Paragraph(_clean_text(company_name or customer_name), st_value),
            Paragraph(_clean_text(short_id), st_value),
        ],
        [
            Paragraph(_clean_text(customer_name), st_value),
            Paragraph(_clean_text("DATUM"), st_label),
        ],
        [
            Paragraph(_clean_text(customer_email), st_value),
            Paragraph(_clean_text(datum), st_value),
        ],
    ]
    meta_tbl = Table(meta_data, colWidths=[95*mm, 70*mm])
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=KC_BORDER))
    story.append(Spacer(1, 5*mm))

    # ── ANREDE ────────────────────────────────────────────
    story.append(Paragraph(
        _clean_text("Sehr geehrte Damen und Herren,"),
        ps("body", fontSize=10, spaceAfter=4)
    ))
    story.append(Paragraph(
        _clean_text(
            "vielen Dank fuer Ihr Vertrauen! Wir freuen uns, "
            "Ihnen hiermit die Auftragsbestaetigung fuer Ihr "
            "neues Website-Projekt zu uebermitteln."
        ),
        ps("body2", fontSize=10, spaceAfter=8)
    ))

    # ── LEISTUNGSUMFANG ───────────────────────────────────
    story.append(Paragraph(
        _clean_text(f"Beauftragtes Paket: {paket['name']}"),
        st_section
    ))
    for item in paket["leistungen"]:
        story.append(Paragraph(_clean_text(f"  +  {item}"), st_item))

    story.append(Spacer(1, 6*mm))

    # ── PREISTABELLE ──────────────────────────────────────
    price_data = [
        [
            Paragraph(_clean_text("Leistung"),
                      ParagraphStyle("th",  fontName=fb, fontSize=9,
                                     textColor=KC_WHITE)),
            Paragraph(_clean_text("Betrag"),
                      ParagraphStyle("th2", fontName=fb, fontSize=9,
                                     textColor=KC_WHITE, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(_clean_text(paket["name"]), st_value),
            Paragraph(_clean_text(f"{paket['netto']:.2f} EUR"), st_right),
        ],
        [
            Paragraph(_clean_text("Nettobetrag"), st_label),
            Paragraph(_clean_text(f"{paket['netto']:.2f} EUR"), st_right),
        ],
        [
            Paragraph(_clean_text("MwSt. 19 %"), st_label),
            Paragraph(_clean_text(f"{mwst:.2f} EUR"), st_right),
        ],
        [
            Paragraph(
                _clean_text("GESAMTBETRAG inkl. MwSt."),
                ParagraphStyle("total", fontName=fb, fontSize=11,
                               textColor=KC_WHITE)
            ),
            Paragraph(
                _clean_text(f"{paket['brutto']:.2f} EUR"),
                ParagraphStyle("totalr", fontName=fb, fontSize=11,
                               textColor=KC_WHITE, alignment=TA_RIGHT)
            ),
        ],
    ]
    price_tbl = Table(price_data, colWidths=[120*mm, 45*mm])
    price_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), KC_TEAL),
        ("BACKGROUND",    (0, 4), (-1, 4), KC_GREEN),
        ("BACKGROUND",    (0, 2), (-1, 3), KC_LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.5, KC_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(price_tbl)
    story.append(Spacer(1, 8*mm))

    # ── NÄCHSTE SCHRITTE ──────────────────────────────────
    story.append(Paragraph(_clean_text("Ihre naechsten Schritte"), st_section))
    lieferzeit = paket["leistungen"][-1].replace("Lieferzeit: ", "")
    steps = [
        "Sie erhalten in Kuerze eine E-Mail mit Ihren Zugangsdaten zum Kundenportal.",
        "Bitte fuellen Sie das Online-Briefing in Ihrem Kundenportal aus (ca. 10 Min.).",
        "Wir melden uns innerhalb von 24 Stunden fuer den Strategy Workshop.",
        f"Ihre neue Website ist in {lieferzeit} fertig.",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(
            _clean_text(f"{i}.  {step}"),
            ps(f"step{i}", fontSize=9, textColor=KC_GRAY,
               leftIndent=4, spaceAfter=4)
        ))

    story.append(Spacer(1, 8*mm))

    # ── UNTERSCHRIFT-PLATZHALTER ──────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=KC_BORDER))
    story.append(Spacer(1, 4*mm))

    sig_data = [
        [
            Paragraph(_clean_text("KOMPAGNON Communications BP GmbH"),
                      ps("sig1", fontSize=9, fontName=fb)),
            Paragraph(_clean_text("Auftraggeber"),
                      ps("sig2", fontSize=9, fontName=fb, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(_clean_text(f"Ort, Datum: Koblenz, {datum}"),
                      ps("sig3", fontSize=8, textColor=KC_GRAY)),
            Paragraph(_clean_text("Ort, Datum: ____________________"),
                      ps("sig4", fontSize=8, textColor=KC_GRAY, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(_clean_text("Unterschrift: ___________________________"),
                      ps("sig5", fontSize=8, textColor=KC_GRAY, spaceAfter=2)),
            Paragraph(_clean_text("Unterschrift: ___________________________"),
                      ps("sig6", fontSize=8, textColor=KC_GRAY,
                         spaceAfter=2, alignment=TA_RIGHT)),
        ],
    ]
    sig_tbl = Table(sig_data, colWidths=[82*mm, 82*mm])
    sig_tbl.setStyle(TableStyle([
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_tbl)

    doc.build(story, onFirstPage=footer_cb, onLaterPages=footer_cb)
    return buffer.getvalue()


def save_auftragsbestaetigung(
    session_id: str,
    customer_name: str,
    customer_email: str,
    company_name: str,
    package_id: str,
    amount_eur: float,
) -> str:
    """
    Generiert PDF, speichert unter uploads/auftragsbestaetigungen/
    und gibt den Dateipfad zurück.
    """
    from pathlib import Path

    datum     = datetime.now().strftime("%d.%m.%Y")
    pdf_bytes = generate_auftragsbestaetigung(
        session_id     = session_id,
        customer_name  = customer_name,
        customer_email = customer_email,
        company_name   = company_name,
        package_id     = package_id,
        amount_eur     = amount_eur,
        datum          = datum,
    )

    upload_dir = Path("uploads") / "auftragsbestaetigungen"
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename  = f"AB-{datum.replace('.', '')}-{session_id[:8]}.pdf"
    file_path = upload_dir / filename
    file_path.write_bytes(pdf_bytes)

    return str(file_path)
