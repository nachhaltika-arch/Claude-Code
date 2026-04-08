"""
PDF Audit Report Generator — Homepage Standard 2025
Generates a professional multi-page PDF using ReportLab.
"""
import json
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


# ═══════════════════════════════════════════════════════════
# Font Registration (DejaVu for full Unicode/Umlaut support)
# ═══════════════════════════════════════════════════════════

def _register_fonts():
    try:
        import reportlab
        font_path = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(font_path, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(font_path, "DejaVuSans-Bold.ttf")))
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"

FONT_NORMAL, FONT_BOLD = _register_fonts()


def _clean_text(text):
    """Normalize Unicode text for PDF rendering."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize("NFC", text)

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
        fontName=FONT_BOLD, fontSize=28, leading=34,
        textColor=KC_DARK, alignment=TA_CENTER, spaceAfter=6*mm,
    ))
    styles.add(ParagraphStyle(
        "KCSubtitle", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=14, leading=18,
        textColor=colors.HexColor("#7f8c8d"), alignment=TA_CENTER, spaceAfter=10*mm,
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
        textColor=colors.HexColor("#95a5a6"),
    ))
    styles.add(ParagraphStyle(
        "KCCenter", parent=styles["Normal"],
        fontName=FONT_NORMAL, fontSize=10, leading=14,
        textColor=KC_DARK, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "KCBold", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=10, leading=14,
        textColor=KC_DARK,
    ))
    return styles


# ═══════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════

def _safe(val, default="-"):
    if val is None:
        return _clean_text(str(default))
    return _clean_text(str(val))


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
    canvas_obj.setFont(FONT_NORMAL, 7)
    canvas_obj.setFillColor(colors.HexColor("#95a5a6"))
    w, h = A4
    canvas_obj.drawString(20*mm, 10*mm,
        _clean_text(f"Homepage Standard - Audit 2025 | KOMPAGNON | Seite {doc.page}"))
    canvas_obj.drawRightString(w - 20*mm, 10*mm,
        _clean_text("Dieses Audit ersetzt keine Rechtsberatung."))
    canvas_obj.restoreState()


# ═══════════════════════════════════════════════════════════
# Chart generators (matplotlib)
# ═══════════════════════════════════════════════════════════

def generate_radar_chart(scores: dict) -> bytes:
    """Draw a spider/radar chart for 6 audit categories. Returns PNG bytes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [
        "SEO & Keywords",
        "Performance",
        "Sicherheit",
        "Inhalt & UX",
        "Rechtliches",
        "GEO / KI-Sichtbarkeit",
    ]
    values = [
        scores.get("seo", 0),
        scores.get("performance", 0),
        scores.get("sicherheit", 0),
        scores.get("ux", 0),
        scores.get("rechtliches", 0),
        scores.get("geo", 0),
    ]

    N = len(labels)
    angles = [2 * math.pi * i / N for i in range(N)]
    angles_closed = angles + [angles[0]]
    values_closed = values + [values[0]]

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Grid
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=6, color="#94a3b8")
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.7)
    ax.xaxis.grid(True, color="#e2e8f0", linewidth=0.7)
    ax.spines["polar"].set_color("#e2e8f0")

    # Axes
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=7, color="#2c3e50")

    # Plot
    ax.plot(angles_closed, values_closed, color="#008eaa", linewidth=2)
    ax.fill(angles_closed, values_closed, color="#008eaa", alpha=0.2)

    plt.tight_layout(pad=1.2)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def generate_donut_chart(positions: dict) -> bytes:
    """Draw a donut chart for keyword position distribution. Returns PNG bytes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["Top 10", "11–20", "21–50", "51–100"]
    values = [
        positions.get("top10", 0),
        positions.get("11_20", 0),
        positions.get("21_50", 0),
        positions.get("51_100", 0),
    ]
    palette = ["#10b981", "#f97316", "#fbbf24", "#ef4444"]

    # If all zeros show a placeholder
    if sum(values) == 0:
        values = [1, 1, 1, 1]
        palette = ["#e2e8f0", "#e2e8f0", "#e2e8f0", "#e2e8f0"]

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
        t.set_color("#2c3e50")
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
    level_color = LEVEL_COLORS.get(level, KC_DANGER)

    rc = audit_data.get("rc_score", 0) or 0
    tp = audit_data.get("tp_score", 0) or 0
    bf = audit_data.get("bf_score", 0) or 0
    si = audit_data.get("si_score", 0) or 0
    se = audit_data.get("se_score", 0) or 0
    ux = audit_data.get("ux_score", 0) or 0

    top_issues = [_clean_text(i) for i in _parse_json_field(audit_data.get("top_issues"))]
    recommendations = [_clean_text(r) for r in _parse_json_field(audit_data.get("recommendations"))]
    ai_summary = _clean_text(audit_data.get("ai_summary", "") or "")

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
                   ParagraphStyle("badge", fontName=FONT_BOLD, fontSize=14,
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
            sc_style.append(("FONTNAME", (-1, i), (-1, i), FONT_BOLD))
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
    proto_style[0] = ("FONTNAME", (0, 0), (0, -1), FONT_BOLD)
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
    story.append(Spacer(1, 8*mm))

    # ── CHARTS: Radar + Donut ───────────────────────────────
    try:
        # Normalize raw scores to 0–10 scale
        radar_scores = {
            "seo":          round((se / 10) * 10, 1),
            "performance":  round((tp / 20) * 10, 1),
            "sicherheit":   round((si / 15) * 10, 1),
            "ux":           round((ux / 5)  * 10, 1),
            "rechtliches":  round((rc / 30) * 10, 1),
            "geo":          round((audit_data.get("geo_score", 0) or 0) / 10 * 10, 1),
        }
        keyword_positions = audit_data.get("keyword_positions") or {}
        if isinstance(keyword_positions, str):
            try:
                keyword_positions = json.loads(keyword_positions)
            except Exception:
                keyword_positions = {}

        radar_png  = generate_radar_chart(radar_scores)
        donut_png  = generate_donut_chart(keyword_positions)

        radar_buf = BytesIO(radar_png)
        donut_buf = BytesIO(donut_png)

        chart_w = 72 * mm   # ~260px equivalent
        radar_img = RLImage(radar_buf, width=chart_w, height=chart_w)
        donut_img = RLImage(donut_buf, width=chart_w, height=chart_w)

        caption_style = ParagraphStyle(
            "ChartCaption", fontName=FONT_NORMAL, fontSize=8,
            textColor=colors.HexColor("#64748b"), alignment=TA_CENTER,
        )
        chart_table = Table(
            [
                [radar_img, donut_img],
                [
                    Paragraph("Kategorien-Radar", caption_style),
                    Paragraph("Keyword-Positionen", caption_style),
                ],
            ],
            colWidths=[chart_w + 4*mm, chart_w + 4*mm],
        )
        chart_table.setStyle(TableStyle([
            ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table)
    except Exception as _chart_err:
        pass  # Charts are optional — don't break PDF generation

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

    # ── PAGE 6: GEO & KI-SICHTBARKEIT ───────────────────────
    story.append(Paragraph("GEO \u0026 KI-Sichtbarkeit", styles["KCHeading"]))
    story.append(Paragraph(
        "KI-Suchsysteme wie ChatGPT, Google AI Overview oder Perplexity crawlen Websites "
        "nach eigenen Regeln. Die folgenden Prüfpunkte zeigen, wie gut die Website für "
        "diese neuen Sichtbarkeitskanäle aufgestellt ist.",
        styles["KCBody"],
    ))
    story.append(Spacer(1, 4*mm))

    llms_txt_ok      = bool(audit_data.get("llms_txt", False))
    robots_ai_ok     = bool(audit_data.get("robots_ai_friendly", False))
    structured_ok    = bool(audit_data.get("structured_data", False))
    ai_mentions_n    = int(audit_data.get("ai_mentions", 0) or 0)
    # Google AI Overview: derive from se_score as proxy if no dedicated field
    ai_overview_ok   = (audit_data.get("se_score", 0) or 0) >= 7

    def _geo_check(ok):
        return Paragraph(
            f'<font color="{"#27ae60" if ok else "#e74c3c"}"><b>{"✓" if ok else "✗"}</b></font>',
            ParagraphStyle("GeoCheck", fontName=FONT_BOLD, fontSize=12, alignment=TA_CENTER),
        )

    geo_header = ["Prüfpunkt", "Status", "Empfehlung"]
    geo_rows = [
        [
            "llms.txt vorhanden",
            _geo_check(llms_txt_ok),
            "Datei unter /llms.txt anlegen" if not llms_txt_ok else "Vorhanden ✓",
        ],
        [
            "robots.txt KI-freundlich",
            _geo_check(robots_ai_ok),
            "GPTBot nicht blockieren" if not robots_ai_ok else "KI-Crawler erlaubt ✓",
        ],
        [
            "Strukturierte Daten",
            _geo_check(structured_ok),
            "Schema.org LocalBusiness ergänzen" if not structured_ok else "Schema.org vorhanden ✓",
        ],
        [
            "KI-Erwähnungen",
            Paragraph(
                f'<font color="{"#27ae60" if ai_mentions_n > 0 else "#e74c3c"}"><b>{ai_mentions_n} gefunden</b></font>',
                ParagraphStyle("GeoMention", fontName=FONT_BOLD, fontSize=10, alignment=TA_CENTER),
            ),
            "Content-Authority aufbauen" if ai_mentions_n == 0 else "Weiter ausbauen",
        ],
        [
            "Google AI Overview",
            _geo_check(ai_overview_ok),
            "Featured Snippets optimieren" if not ai_overview_ok else "Gut aufgestellt ✓",
        ],
    ]

    geo_table = Table(
        [geo_header] + geo_rows,
        colWidths=[55*mm, 25*mm, 80*mm],
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
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF6FF")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
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

    # Derive quick wins from audit data
    quick_wins = []
    if not llms_txt_ok:
        quick_wins.append("llms.txt anlegen (ca. 1 Tag Aufwand)")
    if not structured_ok:
        quick_wins.append("Schema.org LocalBusiness einbauen")
    mobile_ps = audit_data.get("mobile_score", 0) or 0
    if mobile_ps < 50:
        quick_wins.append("Bilder komprimieren \u0026 Lazy Load aktivieren")
    if not robots_ai_ok:
        quick_wins.append("robots.txt: GPTBot-Blockierung entfernen")
    if not quick_wins:
        quick_wins.append("Audit-Score weiter optimieren \u0026 Inhalte aktualisieren")

    midterm = ["Regelmä\u00dfige Blog-Inhalte für SEO-Autorität aufbauen"]
    if level == "Nicht konform":
        midterm.append("SSL, Datenschutzerklärung und Impressum prüfen \u0026 korrigieren")
    if not structured_ok:
        midterm.append("Weitere Schema.org-Typen (FAQPage, Review) ergänzen")

    longterm = [
        "Backlink-Aufbau über lokale Verzeichnisse und Branchenportale",
        "Google Business Profil optimieren und regelmäßig pflegen",
        "KI-Sichtbarkeit: Erwähnungen in Fachartikeln \u0026 Podcasts aufbauen",
    ]

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
        bg_color="#F0FDF4", border_color="#16a34a", phase_label="Phase 1",
    ))
    story.append(Spacer(1, 5*mm))
    story.append(_roadmap_box(
        "Mittelfristig (Monat 1\u20133)", midterm,
        bg_color="#EFF6FF", border_color="#2563eb", phase_label="Phase 2",
    ))
    story.append(Spacer(1, 5*mm))
    story.append(_roadmap_box(
        "Langfristig (Monat 3\u20136)", longterm,
        bg_color="#FAF5FF", border_color="#7c3aed", phase_label="Phase 3",
    ))

    story.append(PageBreak())

    # ── LAST PAGE: CERTIFICATION ────────────────────────────
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Zertifizierungsaussage", styles["KCTitle"]))
    story.append(Spacer(1, 10*mm))

    # Badge again
    badge2_data = [[Paragraph(
        f'<font color="white"><b>{level}</b></font>',
        ParagraphStyle("badge2", fontName=FONT_BOLD, fontSize=16,
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
