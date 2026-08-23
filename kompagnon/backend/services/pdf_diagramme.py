"""Netz- und Ringdiagramm des Audit-Berichts (L-25).

**Warum eigene Datei, 22.08.2026.** `services/pdf_generator.py` hatte 1.424
Zeilen — davon **575 in einer einzigen Funktion**, `generate_audit_report`.
Zwei Diagramme und ein Stufenabzeichen — reine Bilderzeugung mit
matplotlib, die mit dem Aufbau des Berichts nichts zu tun hat.
"""
import math
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from services import brand
import logging

from services.pdf_stil import FONT_BOLD, KC_DANGER, KC_DARK, KC_WHITE, LEVEL_ACCENTS, _clean_text, _matplotlib_schrift

logger = logging.getLogger(__name__)


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
    # Fuenf Ringe, aber nur jeder zweite beschriftet: Fuenf Prozentangaben
    # uebereinander drängten sich auf engem Raum.
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["20%", "", "60%", "", "100%"],
                       fontsize=6, color=brand.TEXT_30)
    # Die Beschriftung lag auf der ersten Achse und damit mitten in der
    # gefuellten Flaeche. Sie wandert an die Achse mit dem kleinsten Wert —
    # dort ist am meisten freier Raum — und bekommt einen hellen Grund.
    # Gesucht ist nicht der kleinste Wert, sondern der schmalste Sektor: Die
    # Beschriftung steht zwischen zwei Achsen, also zaehlt das niedrigste
    # benachbarte Paar.
    sektor = min(range(N), key=lambda i: values[i] + values[(i + 1) % N]) if values else 0
    ax.set_rlabel_position(math.degrees(angles[sektor]) + 180.0 / N)
    for beschriftung in ax.get_yticklabels():
        beschriftung.set_bbox(dict(facecolor="white", edgecolor="none",
                                   alpha=0.75, pad=0.8))
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
