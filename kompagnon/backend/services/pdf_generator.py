"""
PDF Audit Report Generator — Homepage Standard 2025
Generates a professional multi-page PDF using ReportLab.
"""
import json
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
from reportlab.platypus.flowables import HRFlowable

# ═══════════════════════════════════════════════════════════
# Colors
# ═══════════════════════════════════════════════════════════

KC_ROT = colors.HexColor("#c0392b")
KC_DARK = colors.HexColor("#2c3e50")
KC_LIGHT = colors.HexColor("#f8f9fa")
KC_WHITE = colors.white
KC_BORDER = colors.HexColor("#dee2e6")
KC_SUCCESS = colors.HexColor("#27ae60")
KC_WARNING = colors.HexColor("#f39c12")
KC_DANGER = colors.HexColor("#e74c3c")

LEVEL_COLORS = {
    "Homepage Standard Platin": colors.HexColor("#1a3a5c"),
    "Homepage Standard Gold": colors.HexColor("#FFD700"),
    "Homepage Standard Silber": colors.HexColor("#C0C0C0"),
    "Homepage Standard Bronze": colors.HexColor("#CD7F32"),
    "Nicht konform": KC_DANGER,
}

# ═══════════════════════════════════════════════════════════
# Styles
# ═══════════════════════════════════════════════════════════

def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "KCTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=28, leading=34,
        textColor=KC_DARK, alignment=TA_CENTER, spaceAfter=6*mm,
    ))
    styles.add(ParagraphStyle(
        "KCSubtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=14, leading=18,
        textColor=colors.HexColor("#7f8c8d"), alignment=TA_CENTER, spaceAfter=10*mm,
    ))
    styles.add(ParagraphStyle(
        "KCHeading", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=16, leading=20,
        textColor=KC_DARK, spaceBefore=8*mm, spaceAfter=4*mm,
    ))
    styles.add(ParagraphStyle(
        "KCBody", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=KC_DARK, spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        "KCSmall", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8, leading=10,
        textColor=colors.HexColor("#95a5a6"),
    ))
    styles.add(ParagraphStyle(
        "KCCenter", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=KC_DARK, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "KCBold", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10, leading=14,
        textColor=KC_DARK,
    ))
    return styles


# ═══════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════

def _safe(val, default="—"):
    if val is None:
        return str(default)
    return str(val)


def _score_status(score, max_pts):
    if max_pts == 0:
        return "O"
    pct = score / max_pts
    if pct >= 0.8:
        return "O"   # Konform
    if pct >= 0.4:
        return "+"   # Teilweise
    return "-"        # Nicht konform


def _status_color(status):
    if status == "O":
        return KC_SUCCESS
    if status == "+":
        return KC_WARNING
    return KC_DANGER


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
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("FONTSIZE", (0, 1), (-1, -1), 9),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
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
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(colors.HexColor("#95a5a6"))
    w, h = A4
    canvas_obj.drawString(20*mm, 10*mm,
        f"Homepage Standard — Audit 2025 | KOMPAGNON | Seite {doc.page}")
    canvas_obj.drawRightString(w - 20*mm, 10*mm,
        "Dieses Audit ersetzt keine Rechtsberatung.")
    canvas_obj.restoreState()


# ═══════════════════════════════════════════════════════════
# Main generator
# ═══════════════════════════════════════════════════════════

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
    level = audit_data.get("level", "Nicht konform") or "Nicht konform"
    company = audit_data.get("company_name", "Unbekannt") or "Unbekannt"
    url = audit_data.get("website_url", "") or ""
    trade = audit_data.get("trade", "") or ""
    city = audit_data.get("city", "") or ""
    created = audit_data.get("created_at", None)
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except (ValueError, TypeError):
            created = datetime.utcnow()
    elif not created:
        created = datetime.utcnow()
    date_str = created.strftime("%d.%m.%Y")
    level_color = LEVEL_COLORS.get(level, KC_DANGER)

    rc = audit_data.get("rc_score", 0) or 0
    tp = audit_data.get("tp_score", 0) or 0
    bf = audit_data.get("bf_score", 0) or 0
    si = audit_data.get("si_score", 0) or 0
    se = audit_data.get("se_score", 0) or 0
    ux = audit_data.get("ux_score", 0) or 0

    top_issues = _parse_json_field(audit_data.get("top_issues"))
    recommendations = _parse_json_field(audit_data.get("recommendations"))
    ai_summary = audit_data.get("ai_summary", "") or ""

    # ── PAGE 1: COVER ──────────────────────────────────────
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("HOMEPAGE STANDARD", styles["KCTitle"]))
    story.append(Paragraph("Audit- und Zertifizierungsrahmen 2025", styles["KCSubtitle"]))
    story.append(Spacer(1, 15*mm))

    # Score display
    score_text = f'<font size="48" color="{level_color.hexval()}">{total}</font>' \
                 f'<font size="20" color="#95a5a6"> / 100 Punkte</font>'
    story.append(Paragraph(score_text, styles["KCCenter"]))
    story.append(Spacer(1, 6*mm))

    # Level badge
    badge_data = [[Paragraph(f'<font color="white"><b>{level}</b></font>',
                   ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=14,
                                  alignment=TA_CENTER, textColor=KC_WHITE))]]
    badge = Table(badge_data, colWidths=[120*mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), level_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(badge)
    story.append(Spacer(1, 10*mm))

    # Company info
    story.append(Paragraph(f"<b>{company}</b>", styles["KCCenter"]))
    story.append(Paragraph(url, styles["KCCenter"]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"Auditdatum: {date_str}", styles["KCCenter"]))
    story.append(Paragraph("Auditor: KOMPAGNON Communications", styles["KCCenter"]))

    story.append(PageBreak())

    # ── PAGE 2: LEGAL OVERVIEW ──────────────────────────────
    story.append(Paragraph("Rechtliche Grundlagen", styles["KCHeading"]))
    story.append(Paragraph(
        "Die folgenden Gesetze und Standards bilden die Grundlage f\u00fcr die Bewertung.",
        styles["KCBody"],
    ))

    legal_header = ["Rechtsgrundlage", "Pflicht seit", "Betrifft", "Risiko"]
    legal_rows = [
        ["TMG \u00a75 \u2013 Impressumspflicht", "2007", "Alle komm. Websites", "Abmahnung bis 50.000 \u20ac"],
        ["DSGVO \u2013 Datenschutz", "25.05.2018", "Websites mit EU-Besuchern", "Bu\u00dfgeld bis 20 Mio \u20ac"],
        ["TDDDG \u00a725 \u2013 Cookie", "2021/2023", "Websites mit Tracking", "Bu\u00dfgeld, Abmahnungen"],
        ["BFSG \u2013 Barrierefreiheit", "28.06.2025", "Private Anbieter", "Marktaufsicht, Bu\u00dfgeld"],
        ["WCAG 2.1 Level AA", "laufend", "Technische Umsetzung", "Grundlage BFSG"],
        ["Google Core Web Vitals", "Mai 2021", "Alle Websites", "Sichtbarkeitsverlust"],
    ]
    legal_table = Table(
        [legal_header] + legal_rows,
        colWidths=[45*mm, 25*mm, 45*mm, 45*mm],
    )
    legal_table.setStyle(_category_table_style(len(legal_rows)))
    story.append(legal_table)
    story.append(Spacer(1, 8*mm))

    # BFSG notice box
    bfsg_text = (
        '<font color="#2c3e50"><b>Hinweis zum BFSG:</b></font> '
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

    def _cat_section(title, max_pts, score, items):
        """Build a category section: header row + item rows."""
        rows = []
        # Category header
        rows.append([
            Paragraph(f'<b>{title} (max. {max_pts} Pkt.)</b>', styles["KCBold"]),
            "", "", "",
            Paragraph(f'<b>{score} / {max_pts}</b>', styles["KCBold"]),
            "",
        ])
        for item_id, label, pflicht, max_p in items:
            # Distribute score proportionally for display
            item_score = round(score * max_p / max_pts) if max_pts > 0 else 0
            item_score = min(item_score, max_p)
            st = _score_status(item_score, max_p)
            rows.append([item_id, label, pflicht, str(max_p), str(item_score), st])
        return rows

    sc_header = ["ID", "Pr\u00fcfbereich", "Pflicht", "Max.", "Ist", "Status"]

    sc_rows = []
    sc_rows += _cat_section("Rechtliche Compliance", 30, rc, [
        ("RC-01", "Impressum", "Pflicht", 7),
        ("RC-02", "Datenschutzerkl\u00e4rung (DSGVO)", "Pflicht", 7),
        ("RC-03", "Cookie-Consent-Management", "Pflicht", 6),
        ("RC-04", "Barrierefreiheitserkl\u00e4rung (BFSG)", "Pflicht", 4),
        ("RC-05", "Urheberrecht & Lizenzen", "Pflicht", 3),
        ("RC-06", "E-Commerce Pflichten", "Pflicht", 3),
    ])
    sc_rows += _cat_section("Technische Performance", 20, tp, [
        ("TP-01", "LCP (Largest Contentful Paint)", "Pflicht", 5),
        ("TP-02", "CLS (Cumulative Layout Shift)", "Pflicht", 4),
        ("TP-03", "INP (Interaction to Next Paint)", "Empfohlen", 3),
        ("TP-04", "Mobile-First & Responsivit\u00e4t", "Pflicht", 4),
        ("TP-05", "Bildoptimierung", "Empfohlen", 4),
    ])
    sc_rows += _cat_section("Barrierefreiheit", 20, bf, [
        ("BF-01", "Farbkontraste (WCAG 1.4.3)", "Pflicht", 5),
        ("BF-02", "Tastaturzug\u00e4nglichkeit", "Pflicht", 5),
        ("BF-03", "Screenreader-Kompatibilit\u00e4t", "Pflicht", 5),
        ("BF-04", "Lesbarkeit & Verst\u00e4ndlichkeit", "Empfohlen", 5),
    ])
    sc_rows += _cat_section("Sicherheit & Datenschutz", 15, si, [
        ("SI-01", "HTTPS / SSL-Zertifikat", "Pflicht", 4),
        ("SI-02", "Security-Header", "Empfohlen", 4),
        ("SI-03", "DSGVO-konforme Drittanbieter", "Pflicht", 4),
        ("SI-04", "Formularsicherheit & Spam-Schutz", "Empfohlen", 3),
    ])
    sc_rows += _cat_section("SEO & Sichtbarkeit", 10, se, [
        ("SE-01", "Technische SEO-Grundlagen", "Empfohlen", 4),
        ("SE-02", "Strukturierte Daten (Schema.org)", "Optional", 3),
        ("SE-03", "Lokale Auffindbarkeit", "Empfohlen", 3),
    ])
    sc_rows += _cat_section("Inhalt & Nutzererfahrung", 5, ux, [
        ("UX-01", "Erstindruck & Wertversprechen", "Empfohlen", 2),
        ("UX-02", "Call-to-Action & Conversion", "Empfohlen", 2),
        ("UX-03", "Ladegeschwindigkeit UX", "Empfohlen", 1),
    ])

    # Total row
    sc_rows.append([
        Paragraph('<b>GESAMTERGEBNIS</b>', styles["KCBold"]),
        "", "", "100",
        Paragraph(f'<b>{total}</b>', styles["KCBold"]),
        level[:15],
    ])

    sc_table = Table(
        [sc_header] + sc_rows,
        colWidths=[14*mm, 60*mm, 20*mm, 12*mm, 12*mm, 14*mm],
    )
    n = len(sc_rows)
    sc_style = list(BASE_TABLE_STYLE)
    for i in range(1, n + 1):
        row_data = sc_rows[i - 1]
        # Category header rows (have Paragraph in first col)
        if isinstance(row_data[0], Paragraph):
            sc_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#eaf2f8")))
            sc_style.append(("SPAN", (0, i), (3, i)))
        elif i % 2 == 0:
            sc_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
        # Color the status column
        if isinstance(row_data[-1], str) and row_data[-1] in ("O", "+", "-"):
            sc_style.append(("TEXTCOLOR", (-1, i), (-1, i), _status_color(row_data[-1])))
            sc_style.append(("FONTNAME", (-1, i), (-1, i), "Helvetica-Bold"))
            sc_style.append(("ALIGN", (-1, i), (-1, i), "CENTER"))
    # Last row (total)
    sc_style.append(("BACKGROUND", (0, n), (-1, n), KC_DARK))
    sc_style.append(("TEXTCOLOR", (0, n), (-1, n), KC_WHITE))
    sc_table.setStyle(TableStyle(sc_style))
    story.append(sc_table)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Legende: <b>O</b> = Konform | <b>+</b> = Teilweise konform | <b>-</b> = Nicht konform",
        styles["KCSmall"],
    ))

    story.append(PageBreak())

    # ── PAGE 4: AUDIT PROTOCOL ──────────────────────────────
    story.append(Paragraph("Auditprotokoll", styles["KCHeading"]))

    proto_data = [
        ["Website-URL", url],
        ["Auftraggeber / Unternehmen", company],
        ["Branche / Gewerk", _safe(trade, "k.A.")],
        ["Stadt", _safe(city, "k.A.")],
        ["Auditdatum", date_str],
        ["Auditor/in", "KOMPAGNON Communications"],
        ["Audittyp", "Erst-Audit"],
    ]
    proto_table = Table(proto_data, colWidths=[50*mm, 110*mm])
    proto_style = list(BASE_TABLE_STYLE)
    proto_style[2] = ("FONTSIZE", (0, 0), (-1, -1), 10)  # override header font
    proto_style[0] = ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold")
    for i in range(len(proto_data)):
        if i % 2 == 0:
            proto_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
    proto_table.setStyle(TableStyle(proto_style))
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
    sum_data = [
        ["Kategorie", "Ergebnis"],
        ["Rechtliche Compliance (max. 30)", f"{rc} / 30"],
        ["Technische Performance (max. 20)", f"{tp} / 20"],
        ["Barrierefreiheit (max. 20)", f"{bf} / 20"],
        ["Sicherheit & Datenschutz (max. 15)", f"{si} / 15"],
        ["SEO & Sichtbarkeit (max. 10)", f"{se} / 10"],
        ["Inhalt & Nutzererfahrung (max. 5)", f"{ux} / 5"],
        ["GESAMTERGEBNIS", f"{total} / 100"],
    ]
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

    story.append(PageBreak())

    # ── PAGE 5: ISSUES & RECOMMENDATIONS ────────────────────
    story.append(Paragraph("Ma\u00dfnahmen & Empfehlungen", styles["KCHeading"]))

    if top_issues:
        story.append(Paragraph('<font color="#c0392b"><b>Kritische M\u00e4ngel</b></font>', styles["KCBody"]))
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
        story.append(Paragraph('<font color="#27ae60"><b>Empfehlungen</b></font>', styles["KCBody"]))
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

    # ── PAGE 6: CERTIFICATION ───────────────────────────────
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Zertifizierungsaussage", styles["KCTitle"]))
    story.append(Spacer(1, 10*mm))

    # Badge again
    badge2_data = [[Paragraph(
        f'<font color="white"><b>{level}</b></font>',
        ParagraphStyle("badge2", fontName="Helvetica-Bold", fontSize=16,
                       alignment=TA_CENTER, textColor=KC_WHITE),
    )]]
    badge2 = Table(badge2_data, colWidths=[120*mm])
    badge2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), level_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(badge2)
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
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    story.append(sig_table)

    # Build PDF
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
