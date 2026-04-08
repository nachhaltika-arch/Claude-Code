from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from datetime import date


def generate_auftragsbestaetigung(session_id: str, customer_name: str,
                                   customer_email: str, paket: str,
                                   preis: str) -> str:
    short_id = session_id[:12] if session_id else "000000000000"
    path = f"/tmp/auftragsbestaetigung_{short_id}.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    # ── Header ──────────────────────────────────────────────────
    c.setFillColorRGB(0, 0.557, 0.667)  # #008eaa
    c.setFont("Helvetica-Bold", 26)
    c.drawString(2 * cm, h - 2.5 * cm, "KOMPAGNON")
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, h - 4 * cm, "Auftragsbestaetigung")

    # Trennlinie
    c.setStrokeColorRGB(0, 0.557, 0.667)
    c.setLineWidth(2)
    c.line(2 * cm, h - 4.5 * cm, w - 2 * cm, h - 4.5 * cm)

    # ── An / Datum ──────────────────────────────────────────────
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(2 * cm, h - 5.5 * cm, "An:")
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, h - 6.1 * cm, customer_name)
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, h - 6.7 * cm, customer_email)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawRightString(w - 2 * cm, h - 5.5 * cm,
                      f"Datum: {date.today().strftime('%d.%m.%Y')}")
    c.drawRightString(w - 2 * cm, h - 6.1 * cm,
                      f"Bestellnr.: {short_id}")

    # ── Ihr Paket ───────────────────────────────────────────────
    y = h - 8.5 * cm
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(2 * cm, y - 0.3 * cm, w - 4 * cm, 1.2 * cm, fill=1, stroke=0)
    c.setFillColorRGB(0, 0.557, 0.667)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2.3 * cm, y + 0.3 * cm, "Ihr Paket")

    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2.3 * cm, y - 1.2 * cm, paket)
    c.setFont("Helvetica", 11)
    c.drawString(2.3 * cm, y - 1.9 * cm, f"Preis: {preis} inkl. 19% MwSt.")

    # ── Leistungsumfang ─────────────────────────────────────────
    y = h - 12 * cm
    c.setFillColorRGB(0, 0.557, 0.667)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Leistungsumfang")

    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica", 10)
    leistungen = [
        "Professionelles Website-Design (individuell)",
        "Entwicklung & technische Umsetzung",
        "SEO-Grundoptimierung & GEO-Optimierung",
        "30 Tage Support nach Go-Live",
        "Strategie-Workshop (1 Stunde)",
    ]
    for i, item in enumerate(leistungen):
        c.drawString(2.5 * cm, y - (i + 1) * 0.7 * cm, f"\u2022  {item}")

    # ── Unterschrift ────────────────────────────────────────────
    y = h - 18 * cm
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(2 * cm, y, "________________________")
    c.drawString(2 * cm, y - 0.6 * cm, "KOMPAGNON Communications BP GmbH")

    # ── Fusszeile ───────────────────────────────────────────────
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(w / 2, 1.5 * cm,
                        "KOMPAGNON Communications BP GmbH \u00b7 Koblenz \u00b7 kompagnon.eu")

    c.save()
    return path
