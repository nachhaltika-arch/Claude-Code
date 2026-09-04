# -*- coding: utf-8 -*-
"""Die Rechnung zu einer bezahlten Shop-Bestellung (L-100, ORDERS_07).

**Die Reihenfolge ist der ganze Trick.** Erst wird geprüft, ob eine Rechnung
überhaupt entstehen darf, dann das Dokument gebaut, dann abgelegt — und
**erst zuletzt** die Nummer vergeben und die Zeile geschrieben. Eine Nummer,
die vergeben ist, während das Dokument scheitert, ist eine Lücke im
Nummernkreis, die niemand erklären kann; die GoBD verlangen lückenlos.

**Reverse-Charge wird erkannt und abgewiesen, nicht gerechnet.** Ein
Geschäftskunde mit ausländischer EU-USt-IdNr. zahlt ohne deutsche
Umsatzsteuer, und die Rechnung müsste den Übergang der Steuerschuld
ausweisen. ORDERS_07 nimmt das ausdrücklich nicht in diese Ausbaustufe auf —
verlangt aber, dass der Fall auffällt. **Eine falsche Rechnung ist teurer als
eine fehlende: Sie sieht richtig aus.**

**Die Beträge kommen aus der Bestellung, nicht aus dem Katalog.** Der
Katalogpreis kann sich nach dem Kauf geändert haben; die Rechnung weist aus,
was abgebucht wurde.

**Zehn Jahre Aufbewahrungspflicht.** Das Dokument liegt im Objektspeicher
unter `invoices/{jahr}/{nummer}.pdf`, nicht auf dem flüchtigen Dateisystem von
Render — dort wäre es nach dem nächsten Deploy weg.
"""
import logging
from datetime import date, datetime

from sqlalchemy import text

logger = logging.getLogger(__name__)

#: Länderkennungen der EU ohne Deutschland. Trägt ein Geschäftskunde eine
#: USt-IdNr. mit einer davon, ist es ein Reverse-Charge-Fall.
EU_OHNE_DE = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DK", "EE", "EL", "ES", "FI", "FR", "HR",
    "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE",
    "SI", "SK", "XI",           # XI = Nordirland nach dem Brexit-Protokoll
})


def ist_reverse_charge(is_business, ust_id: str) -> bool:
    """Geschäftskunde mit ausländischer EU-USt-IdNr.?

    Leerraum und Kleinschreibung täuschen den Riegel nicht — eine Nummer wie
    `" fr 12345678901 "` ist dieselbe wie `FR12345678901`, und ein Riegel, der
    daran vorbeigeht, ist keiner.
    """
    if not is_business:
        return False
    kennung = "".join((ust_id or "").split()).upper()[:2]
    return kennung in EU_OHNE_DE


def _steuerbetrag(brutto_cents: int, satz) -> int:
    """Der Steueranteil eines Bruttobetrags, kaufmännisch gerundet.

    Aus dem **Brutto** gerechnet, weil `price_brutto` seit dem 21.08. der
    Endpreis ist (L-61): Aus dem Netto zurückzurechnen ergäbe bei krummen
    Sätzen einen Cent Abweichung zur abgebuchten Summe.
    """
    satz = float(satz or 0)
    if satz <= 0:
        return 0
    return int(round(brutto_cents - brutto_cents / (1 + satz / 100)))


def fuer_bestellung(db, order_number: str):
    """Rechnung erzeugen, ablegen und verbuchen.

    Gibt `(eintrag, grund)` zurück: Bei Erfolg das Wörterbuch der Rechnung und
    `""`, sonst `None` und den Grund im Klartext.
    """
    from modelle_buch import BookOrder
    from services import produktablage, rechnung_pdf, rechnungsnummer

    eintrag = db.query(BookOrder).filter(
        BookOrder.order_number == order_number).first()
    if not eintrag:
        return None, "Bestellung nicht gefunden"

    if eintrag.payment_status not in ("paid", "delivered"):
        return None, "Für eine unbezahlte Bestellung gibt es keine Rechnung"

    if ist_reverse_charge(eintrag.is_business, eintrag.buyer_vat_id):
        # Erkannt und abgewiesen — nicht falsch gerechnet.
        logger.error(
            "Bestellung %s ist ein Reverse-Charge-Fall (USt-IdNr. %r): "
            "Rechnung nicht erzeugt, bitte von Hand ausstellen",
            order_number, eintrag.buyer_vat_id)
        return None, ("Reverse-Charge: Der Übergang der Steuerschuld ist in "
                      "dieser Ausbaustufe nicht abgebildet. Die Rechnung muss "
                      "von Hand ausgestellt werden.")

    # Schon vorhanden? Eine zweite Nummer für denselben Vorgang reisst eine
    # Lücke in den Kreis.
    vorhanden = db.execute(text(
        "SELECT invoice_number, amount_gross FROM invoices "
        "WHERE line_item LIKE :muster ORDER BY id DESC LIMIT 1"
    ), {"muster": f"%{order_number}%"}).fetchone()
    if vorhanden:
        return ({"invoice_number": vorhanden[0],
                 "amount_gross_cents": int(round(float(vorhanden[1]) * 100))},
                "")

    # **Vor der Nummer prüfen, ob die Ablage überhaupt annehmen kann.** Sonst
    # ist die Nummer vergeben und das Dokument nirgends.
    fehlt = produktablage.was_fehlt()
    if fehlt:
        logger.error("Rechnung fuer %s nicht erzeugt — Ablage fehlt: %s",
                     order_number, ", ".join(fehlt))
        return None, f"Dateiablage nicht eingerichtet: {', '.join(fehlt)}"

    brutto = int(eintrag.price_gross_cents or 0)
    satz = float(eintrag.tax_rate or 0)
    steuer = _steuerbetrag(brutto, satz)
    heute = date.today()

    produktname = db.execute(text(
        "SELECT name FROM products WHERE slug = :s"),
        {"s": eintrag.product_slug}).scalar() or eintrag.product_slug or ""

    nummer = rechnungsnummer.naechste(db, jahr=heute.year)

    daten = {
        "invoice_number": nummer,
        "invoice_date": heute.strftime("%d.%m.%Y"),
        "service_date": (eintrag.delivered_at or eintrag.created_at
                         or datetime.utcnow()).strftime("%d.%m.%Y"),
        "paid_date": (eintrag.delivered_at or datetime.utcnow())
        .strftime("%d.%m.%Y"),
        "customer_name": f"{eintrag.first_name} {eintrag.last_name}".strip(),
        "customer_company": eintrag.company or "",
        "customer_address": eintrag.ship_street or "",
        "customer_email": eintrag.email or "",
        "line_item": produktname,
        "amount_net_cents": brutto - steuer,
        "tax_cents": steuer,
        "amount_gross_cents": brutto,
        "tax_rate": int(satz) if float(satz).is_integer() else satz,
        "order_number": order_number,
        "payment_method": "Kreditkarte",
    }

    pfad = f"invoices/{heute.year}/{nummer}.pdf"
    if not produktablage.ablegen(pfad, rechnung_pdf.erzeugen(daten)):
        # Die Nummer ist vergeben; die Transaktion wird **nicht** bestätigt,
        # also verfällt sie mit dem Rücksetzen. Der Aufrufer schliesst.
        db.rollback()
        logger.error("Rechnung %s nicht abgelegt — Nummer verfaellt", nummer)
        return None, "Die Rechnung konnte nicht abgelegt werden"

    db.execute(text("""
        INSERT INTO invoices (invoice_number, amount_net, tax_rate,
                              amount_gross, status, customer_email,
                              customer_name, line_item, paid_at)
        VALUES (:nr, :netto, :satz, :brutto, 'bezahlt', :mail, :name,
                :posten, NOW())
    """), {
        "nr": nummer,
        "netto": daten["amount_net_cents"] / 100,
        "satz": satz,
        "brutto": brutto / 100,
        "mail": daten["customer_email"],
        "name": daten["customer_name"],
        # Die Bestellnummer steht im Posten: Sie ist die Brücke zurück, und
        # eine eigene Spalte dafür gäbe es in `invoices` nicht.
        "posten": f"{produktname} (Bestellung {order_number})",
    })
    db.commit()

    logger.info("Rechnung %s fuer Bestellung %s erzeugt (%d Cent)",
                nummer, order_number, brutto)
    return daten, ""


def pfad_zu(invoice_number: str, jahr: int = None) -> str:
    """Wo die Rechnung liegt. Eine Stelle, damit Schreiben und Lesen
    denselben Pfad bilden."""
    jahr = jahr or date.today().year
    return f"invoices/{jahr}/{invoice_number}.pdf"
