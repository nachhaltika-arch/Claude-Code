from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import date
import os


def generate_invoice_pdf(invoice: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Header
    c.setFillColorRGB(0, 0.557, 0.667)
    c.rect(0, h - 3 * cm, w, 3 * cm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, h - 1.8 * cm, "KOMPAGNON")
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, h - 2.4 * cm, "Communications BP GmbH \u00b7 kompagnon.eu")

    # Rechnungsnummer rechts
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(1, 1, 1)
    c.drawRightString(w - 2 * cm, h - 1.8 * cm, f"Rechnung {invoice.get('invoice_number', '')}")

    # Absender
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, h - 4 * cm, "KOMPAGNON Communications BP GmbH")
    c.drawString(2 * cm, h - 4.5 * cm, os.getenv("COMPANY_ADDRESS", "Musterstrasse 1, 56000 Koblenz"))

    # Empfaenger
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, h - 6 * cm, invoice.get("customer_name", ""))
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, h - 6.6 * cm, invoice.get("customer_email", ""))

    # Rechnungsdetails
    c.setFont("Helvetica", 10)
    c.drawString(12 * cm, h - 6 * cm, f"Datum: {date.today().strftime('%d.%m.%Y')}")
    c.drawString(12 * cm, h - 6.6 * cm, f"Faellig: {invoice.get('due_date', '')}")

    # Trennlinie
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(2 * cm, h - 7.5 * cm, w - 2 * cm, h - 7.5 * cm)

    # Tabelle Header
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(2 * cm, h - 8.5 * cm, w - 4 * cm, 0.8 * cm, fill=1, stroke=0)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.3 * cm, h - 8.1 * cm, "Leistung")
    c.drawString(13 * cm, h - 8.1 * cm, "Einzelpreis")
    c.drawString(16 * cm, h - 8.1 * cm, "Gesamt")

    # Zeile
    c.setFont("Helvetica", 10)
    c.drawString(2.3 * cm, h - 9.5 * cm, invoice.get("line_item", "Website-Pflege & SEO"))
    net = float(invoice.get("amount_net", 89))
    c.drawString(13 * cm, h - 9.5 * cm, f"{net:.2f} \u20ac")
    c.drawString(16 * cm, h - 9.5 * cm, f"{net:.2f} \u20ac")

    # Summen
    tax = net * float(invoice.get("tax_rate", 19)) / 100
    gross = net + tax
    c.line(2 * cm, h - 10.5 * cm, w - 2 * cm, h - 10.5 * cm)
    c.drawString(13 * cm, h - 11 * cm, f"Netto: {net:.2f} \u20ac")
    c.drawString(13 * cm, h - 11.6 * cm, f"MwSt. {invoice.get('tax_rate', 19)}%: {tax:.2f} \u20ac")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(13 * cm, h - 12.4 * cm, f"Gesamt: {gross:.2f} \u20ac")

    # Bankdaten
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    iban = os.getenv("BANK_IBAN", "DE00 0000 0000 0000 0000 00")
    bic = os.getenv("BANK_BIC", "XXXXXXXX")
    bank = os.getenv("BANK_NAME", "Musterbank")
    c.drawString(2 * cm, 2 * cm, f"Bankverbindung: {bank} \u00b7 IBAN: {iban} \u00b7 BIC: {bic}")

    c.save()
    return buf.getvalue()
