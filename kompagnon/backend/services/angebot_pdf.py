"""
Angebots-PDF Generator — KOMPAGNON Homepage Standard
Generiert ein professionelles 4-seitiges Angebots-PDF aus Audit-Daten.
"""
import os
import unicodedata
from io import BytesIO
from datetime import datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonts ─────────────────────────────────────────────────────────────────────

def _register_fonts():
    try:
        import reportlab
        p = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        pdfmetrics.registerFont(TTFont("DejaVu",      os.path.join(p, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(p, "DejaVuSans-Bold.ttf")))
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"

FN, FNB = _register_fonts()

# ── Farben ─────────────────────────────────────────────────────────────────────

KC_BLUE    = colors.HexColor("#0d6efd")
KC_DARK    = colors.HexColor("#1a2332")
KC_TEAL    = colors.HexColor("#008eaa")
KC_LIGHT   = colors.HexColor("#f8f9fa")
KC_SUCCESS = colors.HexColor("#1D9E75")
KC_DANGER  = colors.HexColor("#E24B4A")
KC_WARNING = colors.HexColor("#f59e0b")
KC_WHITE   = colors.white
KC_BORDER  = colors.HexColor("#dee2e6")
KC_GRAY    = colors.HexColor("#6c757d")
KC_ORANGE  = colors.HexColor("#fd7e14")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def _c(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text))


def _score_color(score):
    s = int(score or 0)
    if s >= 70:
        return KC_SUCCESS
    if s >= 40:
        return KC_ORANGE
    return KC_DANGER


def _angebot_nr(audit_id):
    return f"ANG-{audit_id}-{datetime.now().strftime('%Y%m%d')}"


def _styles():
    base = getSampleStyleSheet()
    add = lambda name, **kw: base.add(ParagraphStyle(name, parent=base["Normal"], fontName=FN, **kw))
    add("ANG_Small",   fontSize=8,  leading=11, textColor=KC_GRAY)
    add("ANG_Body",    fontSize=10, leading=14)
    add("ANG_Bold",    fontSize=10, leading=14, fontName=FNB)
    add("ANG_H1",      fontSize=20, leading=26, fontName=FNB, textColor=KC_DARK)
    add("ANG_H2",      fontSize=14, leading=18, fontName=FNB, textColor=KC_DARK)
    add("ANG_Center",  fontSize=10, leading=14, alignment=TA_CENTER)
    add("ANG_CenterB", fontSize=10, leading=14, alignment=TA_CENTER, fontName=FNB)
    add("ANG_Teal",    fontSize=28, leading=34, fontName=FNB, textColor=KC_TEAL)
    add("ANG_Sub",     fontSize=11, leading=15, textColor=KC_GRAY)
    add("ANG_BigNum",  fontSize=32, leading=38, fontName=FNB, alignment=TA_CENTER)
    add("ANG_Price",   fontSize=32, leading=38, fontName=FNB, alignment=TA_CENTER, textColor=KC_WHITE)
    add("ANG_White",   fontSize=10, leading=14, textColor=KC_WHITE, alignment=TA_CENTER)
    add("ANG_WhiteB",  fontSize=12, leading=16, textColor=KC_WHITE, alignment=TA_CENTER, fontName=FNB)
    add("ANG_Danger",  fontSize=10, leading=14, textColor=KC_DANGER)
    return base


# ── Seitennummer-Canvas ────────────────────────────────────────────────────────

class _NumberedCanvas:
    """Wird als onFirstPage / onLaterPages verwendet."""
    def __init__(self, angebot_nr):
        self.nr = angebot_nr

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(FN, 8)
        canvas.setFillColor(KC_GRAY)
        footer = f"{self.nr}  |  Seite {doc.page}"
        canvas.drawRightString(PAGE_W - MARGIN, 12 * mm, footer)
        canvas.restoreState()


# ══════════════════════════════════════════════════════════════════════════════
# Hauptfunktion
# ══════════════════════════════════════════════════════════════════════════════

def generate_angebot_pdf(audit_data: dict) -> bytes:
    buf = BytesIO()
    S = _styles()
    audit_id   = audit_data.get("id", 0)
    ang_nr     = _angebot_nr(audit_id)
    today      = datetime.now()
    valid_date = (today + timedelta(days=30)).strftime("%d.%m.%Y")
    today_str  = today.strftime("%d.%m.%Y")

    # Audit-Daten
    company    = _c(audit_data.get("company_name") or "Ihr Unternehmen")
    website    = _c(audit_data.get("website_url") or "")
    city       = _c(audit_data.get("city") or "")
    trade      = _c(audit_data.get("trade") or "")
    score      = int(audit_data.get("total_score") or 0)
    level      = _c(audit_data.get("level") or "Nicht konform")
    top_issues = audit_data.get("top_issues") or audit_data.get("top_problems") or []
    if isinstance(top_issues, str):
        import json
        try:
            top_issues = json.loads(top_issues)
        except Exception:
            top_issues = [l.strip() for l in top_issues.split("\n") if l.strip()]

    # Kategorie-Scores
    cat_scores = [
        ("Rechtliche Konformität",  audit_data.get("rc_score")),
        ("Technische Performance",  audit_data.get("tp_score")),
        ("Briefing & Positionierung", audit_data.get("bf_score")),
        ("SEO & Sichtbarkeit",      audit_data.get("si_score")),
        ("Schema & Strukturdaten",  audit_data.get("se_score")),
        ("UX & Design",             audit_data.get("ux_score")),
    ]

    # Kontakt aus Umgebung
    contact_email = os.environ.get("SMTP_FROM") or os.environ.get("FROM_EMAIL") or "info@kompagnon.eu"

    footer_cb = _NumberedCanvas(ang_nr)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=22 * mm,
    )

    story = []
    usable_w = PAGE_W - 2 * MARGIN

    # ══════════════════════════════════════════════════════════════
    # SEITE 1 — Deckblatt
    # ══════════════════════════════════════════════════════════════

    # Logo-Zeile
    story.append(Table(
        [[Paragraph("KOMPAGNON", S["ANG_Teal"]),
          Paragraph("Communications BP GmbH", S["ANG_Sub"])]],
        colWidths=[usable_w * 0.45, usable_w * 0.55],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",  (1, 0), (1, 0),  "RIGHT"),
        ])
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=KC_TEAL, spaceAfter=8 * mm))

    # Haupttitel
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("ANGEBOT", ParagraphStyle(
        "ANG_Big", parent=S["Normal"], fontName=FNB, fontSize=36, leading=42,
        textColor=KC_DARK, alignment=TA_CENTER,
    )))
    story.append(Paragraph("Website-Redesign &amp; Digitale Optimierung",
                            ParagraphStyle("ANG_Sub2", parent=S["Normal"], fontName=FN,
                                           fontSize=14, leading=18, textColor=KC_GRAY, alignment=TA_CENTER)))
    story.append(Spacer(1, 8 * mm))

    # Score-Box
    score_color = _score_color(score)
    score_style = ParagraphStyle("ScoreNum", parent=S["Normal"],
                                 fontName=FNB, fontSize=48, leading=54,
                                 textColor=score_color, alignment=TA_CENTER)
    score_box = Table(
        [[Paragraph("Aktuelle Website-Bewertung:", S["ANG_CenterB"])],
         [Paragraph(str(score), score_style)],
         [Paragraph("von 100 Punkten", S["ANG_Center"])],
         [Spacer(1, 4 * mm)],
         [Paragraph(f"Zertifizierungsstufe: <b>{level}</b>", S["ANG_Center"])],
        ],
        colWidths=[usable_w * 0.7],
        style=TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), KC_LIGHT),
            ("ROUNDEDCORNERS", (0, 0), (-1, -1), [8]),
            ("BOX",         (0, 0), (-1, -1), 1, KC_BORDER),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",  (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
        hAlign="CENTER",
    )
    story.append(score_box)
    story.append(Spacer(1, 8 * mm))

    # Firmeninfo
    info_lines = [company]
    if website: info_lines.append(website)
    if city:    info_lines.append(city)
    if trade:   info_lines.append(trade)
    for line in info_lines:
        story.append(Paragraph(_c(line), ParagraphStyle(
            "InfoL", parent=S["Normal"], fontName=FN, fontSize=11, leading=16,
            alignment=TA_CENTER, textColor=KC_DARK,
        )))
    story.append(Spacer(1, 10 * mm))

    # Angebotsmeta
    meta_table = Table(
        [["Angebotsnummer:", ang_nr],
         ["Datum:", today_str],
         ["Gültig bis:", valid_date]],
        colWidths=[usable_w * 0.35, usable_w * 0.35],
        hAlign="CENTER",
        style=TableStyle([
            ("FONTNAME",  (0, 0), (0, -1), FNB),
            ("FONTNAME",  (1, 0), (1, -1), FN),
            ("FONTSIZE",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
            ("TEXTCOLOR", (0, 0), (-1, -1), KC_DARK),
        ]),
    )
    story.append(meta_table)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # SEITE 2 — Ausgangslage & Handlungsbedarf
    # ══════════════════════════════════════════════════════════════

    story.append(Paragraph("Wo Ihre Website heute steht", S["ANG_H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=KC_BORDER, spaceAfter=6 * mm))

    # Kategorie-Tabelle
    cat_header = [
        Paragraph("Kategorie", S["ANG_Bold"]),
        Paragraph("Score", S["ANG_Bold"]),
        Paragraph("Status", S["ANG_Bold"]),
    ]
    cat_rows = [cat_header]
    for cat_name, cat_val in cat_scores:
        v = int(cat_val or 0)
        if v >= 70:
            status_text = "✓  OK"
            status_color = KC_SUCCESS
        elif v >= 40:
            status_text = "⚠  Verbesserung nötig"
            status_color = KC_ORANGE
        else:
            status_text = "✗  Handlungsbedarf"
            status_color = KC_DANGER
        cat_rows.append([
            Paragraph(_c(cat_name), S["ANG_Body"]),
            Paragraph(str(v), S["ANG_Bold"]),
            Paragraph(status_text, ParagraphStyle(
                f"St{v}", parent=S["Normal"], fontName=FNB, fontSize=10,
                leading=14, textColor=status_color,
            )),
        ])

    cat_table = Table(
        cat_rows,
        colWidths=[usable_w * 0.55, usable_w * 0.15, usable_w * 0.30],
        style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  KC_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  KC_WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  FNB),
            ("FONTSIZE",      (0, 0), (-1, 0),  10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [KC_WHITE, KC_LIGHT]),
            ("BOX",           (0, 0), (-1, -1), 1, KC_BORDER),
            ("INNERGRID",     (0, 0), (-1, -1), 0.5, KC_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]),
    )
    story.append(cat_table)
    story.append(Spacer(1, 8 * mm))

    # Top-Prioritäten
    story.append(Paragraph("Top-Prioritäten", S["ANG_H2"]))
    story.append(Spacer(1, 3 * mm))
    issues_to_show = list(top_issues)[:3] if top_issues else ["Bitte Audit-Ergebnis prüfen"]
    for i, issue in enumerate(issues_to_show, 1):
        story.append(Paragraph(
            f"<b>{i}.</b>  {_c(str(issue))}",
            ParagraphStyle(f"Issue{i}", parent=S["Normal"], fontName=FN, fontSize=10,
                           leading=14, textColor=KC_DANGER, leftIndent=10, spaceAfter=4),
        ))
    story.append(Spacer(1, 6 * mm))

    # Infokasten
    info_box = Table(
        [[Paragraph(
            "Diese Mängel kosten Sie täglich potenzielle Kunden. "
            "Jeder Tag ohne professionelle Website ist ein verlorener Auftrag.",
            ParagraphStyle("IB", parent=S["Normal"], fontName=FN, fontSize=10,
                           leading=14, textColor=KC_DARK),
        )]],
        colWidths=[usable_w],
        style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), KC_LIGHT),
            ("BOX",           (0, 0), (-1, -1), 1, KC_BORDER),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
    )
    story.append(info_box)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # SEITE 3 — Unser Angebot
    # ══════════════════════════════════════════════════════════════

    story.append(Paragraph("Das KOMPAGNON Homepage Standard Paket", S["ANG_H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=KC_BORDER, spaceAfter=6 * mm))

    leistungen = [
        ("WordPress-Website nach Homepage Standard 2025",   True),
        ("SEO &amp; GEO/KI-Optimierung",                   True),
        ("Google Business Profil Einrichtung",              True),
        ("Strategy Workshop (Briefing)",                    True),
        ("14 Werktage Lieferzeit",                          True),
        ("6 Monate Nachbetreuung &amp; Support",            True),
        ("Zertifizierung nach Homepage Standard 2025",      True),
    ]
    check_style = ParagraphStyle("Chk", parent=S["Normal"], fontName=FNB,
                                 fontSize=11, textColor=KC_SUCCESS, alignment=TA_CENTER)
    leist_header = [Paragraph("Leistung", S["ANG_Bold"]),
                    Paragraph("Enthalten", S["ANG_Bold"])]
    leist_rows = [leist_header] + [
        [Paragraph(_c(name), S["ANG_Body"]),
         Paragraph("✓" if ok else "–", check_style)]
        for name, ok in leistungen
    ]
    leist_table = Table(
        leist_rows,
        colWidths=[usable_w * 0.78, usable_w * 0.22],
        style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  KC_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  KC_WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  FNB),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [KC_WHITE, KC_LIGHT]),
            ("BOX",           (0, 0), (-1, -1), 1, KC_BORDER),
            ("INNERGRID",     (0, 0), (-1, -1), 0.5, KC_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ]),
    )
    story.append(leist_table)
    story.append(Spacer(1, 8 * mm))

    # Preisbox
    price_box = Table(
        [[Paragraph("2.000,00 €", S["ANG_Price"])],
         [Paragraph("netto zzgl. 19% MwSt.", S["ANG_White"])],
         [Spacer(1, 4 * mm)],
         [Paragraph("2.380,00 € brutto", S["ANG_WhiteB"])],
        ],
        colWidths=[usable_w * 0.6],
        hAlign="CENTER",
        style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), KC_BLUE),
            ("ROUNDEDCORNERS",(0, 0), (-1, -1), [10]),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]),
    )
    story.append(price_box)
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "Einmaliger Festpreis — keine versteckten Kosten",
        ParagraphStyle("Hinweis", parent=S["Normal"], fontName=FNB, fontSize=10,
                       leading=14, textColor=KC_GRAY, alignment=TA_CENTER),
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # SEITE 4 — Nächste Schritte & Unterschrift
    # ══════════════════════════════════════════════════════════════

    story.append(Paragraph("So geht es weiter", S["ANG_H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=KC_BORDER, spaceAfter=6 * mm))

    steps = [
        ("1", "Angebot annehmen &amp; Termin vereinbaren",
         "Unterschreiben Sie dieses Angebot und kontaktieren Sie uns für einen Ersttermin."),
        ("2", "Strategy Workshop (ca. 90 Min., kostenlos)",
         "Wir analysieren gemeinsam Ihre Ziele, Zielgruppe und Wettbewerber."),
        ("3", "Go-Live in 14 Werktagen",
         "Ihre neue, zertifizierte Website ist fertig und live geschaltet."),
    ]
    for num, title, desc in steps:
        step_box = Table(
            [[Paragraph(num, ParagraphStyle(
                  f"SN{num}", parent=S["Normal"], fontName=FNB, fontSize=18,
                  textColor=KC_WHITE, alignment=TA_CENTER)),
              Table([[Paragraph(_c(title), ParagraphStyle(
                          f"ST{num}", parent=S["Normal"], fontName=FNB,
                          fontSize=11, leading=14, textColor=KC_DARK))],
                     [Paragraph(_c(desc), S["ANG_Small"])]],
                    colWidths=[usable_w - 60],
                    style=TableStyle([
                        ("TOPPADDING",    (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]))]],
            colWidths=[40, usable_w - 40],
            style=TableStyle([
                ("BACKGROUND",  (0, 0), (0, 0),  KC_TEAL),
                ("ALIGN",       (0, 0), (0, 0),  "CENTER"),
                ("VALIGN",      (0, 0), (-1, -1),"MIDDLE"),
                ("BOX",         (0, 0), (-1, -1), 1, KC_BORDER),
                ("LEFTPADDING", (0, 0), (0, 0),  0),
                ("LEFTPADDING", (1, 0), (1, 0),  10),
                ("TOPPADDING",  (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING",(0,0), (-1, -1), 10),
            ]),
        )
        story.append(step_box)
        story.append(Spacer(1, 5 * mm))

    story.append(Spacer(1, 8 * mm))

    # Unterschriftsfeld
    sig_table = Table(
        [["Datum:", "", "Unterschrift Auftraggeber:"],
         [Spacer(1, 12 * mm), "", Spacer(1, 12 * mm)],
         [HRFlowable(width="100%", thickness=1, color=KC_DARK), "",
          HRFlowable(width="100%", thickness=1, color=KC_DARK)],
        ],
        colWidths=[usable_w * 0.35, usable_w * 0.10, usable_w * 0.55],
        style=TableStyle([
            ("FONTNAME",   (0, 0), (-1, 0), FNB),
            ("FONTSIZE",   (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    )
    story.append(sig_table)
    story.append(Spacer(1, 10 * mm))

    # Kontaktblock
    story.append(HRFlowable(width="100%", thickness=1, color=KC_BORDER, spaceBefore=4 * mm, spaceAfter=4 * mm))
    story.append(Paragraph(
        f"<b>KOMPAGNON Communications BP GmbH</b> &nbsp;·&nbsp; "
        f"kompagnon.eu &nbsp;·&nbsp; {_c(contact_email)}",
        ParagraphStyle("Contact", parent=S["Normal"], fontName=FN, fontSize=9,
                       leading=13, textColor=KC_GRAY, alignment=TA_CENTER),
    ))

    # ── Bauen ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=footer_cb, onLaterPages=footer_cb)
    return buf.getvalue()
