# -*- coding: utf-8 -*-
"""Das Rechnungsdokument zu einer Shop-Bestellung (L-100, ORDERS_07).

**Warum eigen und nicht `invoice_pdf.py` erweitert.** Der vorhandene Erzeuger
bedient die Projektrechnungen und druckt weder USt-IdNr. noch Steuerbetrag
noch Leistungsdatum. Ihn umzubauen hieße, ein Dokument zu ändern, das bereits
ausgestellt wurde — bei Steuerbelegen ist das die falsche Richtung. Der
Befund, dass **auch die Projektrechnung** Pflichtangaben vermissen lässt,
gehört gemeldet und nicht nebenbei mitgeändert.

**Ohne Kompression.** Ein Rechnungs-PDF ist ein paar Kilobyte; die Ersparnis
ist nichts wert. Der Gewinn ist, dass der Text im Dokument **auffindbar**
bleibt — die Prüfungen suchen die Pflichtangaben in den Bytes des fertigen
Dokuments und nicht in dem Wörterbuch, aus dem es entstand. Genau diese
Unterscheidung hat der StripeObject-Fehler am 27.08. gekostet: Alle Prüfungen
waren grün und keine je am Gegenstand.

**Die Pflichtangaben stehen in § 14 UStG.** Sie sind hier einzeln benannt,
damit beim nächsten Lesen nachvollziehbar ist, warum jede Zeile da ist — und
damit auffällt, wenn eine verschwindet.
"""
import os
from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

#: Der Aussteller. Aus der Umgebung überschreibbar, damit eine Umfirmierung
#: keinen Deploy braucht — die Vorgaben sind die Angaben des Impressums.
AUSSTELLER = {
    "name": "KOMPAGNON Communications BP GmbH",
    "strasse": "Marienfelder Straße 52",
    "ort": "56070 Koblenz",
    "ustid": "DE317883455",
}

#: Dark Teal aus der Tool-CI.
KC_DARK = (0, 0.31, 0.35)


def _wert(schluessel: str) -> str:
    return os.getenv(f"COMPANY_{schluessel.upper()}", "").strip() \
        or AUSSTELLER[schluessel]


def _euro(cents: int) -> str:
    """Cent → `149,00 €` mit deutschem Komma."""
    return f"{(cents or 0) / 100:.2f}".replace(".", ",") + " €"


def erzeugen(daten: dict) -> bytes:
    """Das Dokument. `daten` kommt aus `services/rechnung.fuer_bestellung`."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    # Siehe Kopftext: Der Text soll im Dokument auffindbar bleiben.
    c.setPageCompression(0)
    w, h = A4

    # ── Kopf ─────────────────────────────────────────────────────────
    c.setFillColorRGB(*KC_DARK)
    c.rect(0, h - 3 * cm, w, 3 * cm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, h - 1.9 * cm, "KOMPAGNON")
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(w - 2 * cm, h - 1.9 * cm,
                      f"Rechnung {daten['invoice_number']}")

    # ── Aussteller: Name, Anschrift, USt-IdNr. ───────────────────────
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica", 9)
    y = h - 4.0 * cm
    for zeile in (_wert("name"), _wert("strasse"), _wert("ort"),
                  f"USt-IdNr. {_wert('ustid')}"):
        c.drawString(2 * cm, y, zeile)
        y -= 0.45 * cm

    # ── Empfänger: Name und Anschrift ────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, h - 6.6 * cm, daten.get("customer_name", ""))
    c.setFont("Helvetica", 10)
    y = h - 7.15 * cm
    for zeile in (daten.get("customer_company", ""),
                  daten.get("customer_address", ""),
                  daten.get("customer_email", "")):
        if zeile:
            c.drawString(2 * cm, y, zeile)
            y -= 0.5 * cm

    # ── Rechnungsdatum und Leistungsdatum ────────────────────────────
    # Beide sind Pflicht und sind **nicht dasselbe**: Das Leistungsdatum ist
    # der Tag der Bereitstellung, das Rechnungsdatum der Tag der Ausstellung.
    c.setFont("Helvetica", 10)
    c.drawString(12 * cm, h - 6.6 * cm,
                 f"Rechnungsdatum: {daten['invoice_date']}")
    c.drawString(12 * cm, h - 7.15 * cm,
                 f"Leistungsdatum: {daten['service_date']}")

    # ── Die Leistung ─────────────────────────────────────────────────
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(2 * cm, h - 9.2 * cm, w - 2 * cm, h - 9.2 * cm)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2 * cm, h - 9.9 * cm, "Bezeichnung")
    c.drawRightString(12.5 * cm, h - 9.9 * cm, "Menge")
    c.drawRightString(w - 2 * cm, h - 9.9 * cm, "Betrag")

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, h - 10.7 * cm, daten.get("line_item", ""))
    c.drawRightString(12.5 * cm, h - 10.7 * cm, "1")
    c.drawRightString(w - 2 * cm, h - 10.7 * cm,
                      _euro(daten["amount_net_cents"]))

    # ── Netto, Steuersatz, Steuerbetrag, Brutto ──────────────────────
    c.line(2 * cm, h - 11.4 * cm, w - 2 * cm, h - 11.4 * cm)
    y = h - 12.1 * cm
    for beschriftung, betrag in (
        ("Nettobetrag", _euro(daten["amount_net_cents"])),
        (f"zzgl. {daten['tax_rate']} % Umsatzsteuer",
         _euro(daten["tax_cents"])),
    ):
        c.drawString(12 * cm, y, beschriftung)
        c.drawRightString(w - 2 * cm, y, betrag)
        y -= 0.55 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(12 * cm, y - 0.2 * cm, "Gesamtbetrag")
    c.drawRightString(w - 2 * cm, y - 0.2 * cm,
                      _euro(daten["amount_gross_cents"]))

    # ── Hinweis auf die erfolgte Zahlung ─────────────────────────────
    # Ohne ihn liest sich eine bezahlte Rechnung wie eine Forderung, und der
    # Käufer überweist ein zweites Mal.
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawString(2 * cm, y - 1.6 * cm,
                 f"Der Betrag wurde am {daten['paid_date']} per "
                 f"{daten.get('payment_method', 'Kreditkarte')} bezahlt. "
                 f"Diese Rechnung ist bereits bezahlt — bitte nicht "
                 f"überweisen.")
    c.drawString(2 * cm, y - 2.1 * cm,
                 f"Bestellung {daten.get('order_number', '')}")

    c.save()
    return buf.getvalue()
