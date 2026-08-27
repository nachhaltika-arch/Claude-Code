# -*- coding: utf-8 -*-
"""Eine Bestellung eines Katalogprodukts anlegen (L-100, ORDERS_03).

**Warum hier und nicht in einem vierten Kassen-Router.** ORDERS_03 verlangt
`POST /api/shop/checkout` in einer neuen `routers/shop.py`. Es gibt aber
bereits drei Kassen — `payments` (Websprints), `geo_payments` (Abo) und
`buch`. Und `routers/buch.py` fuehrt genau den Ablauf aus, den der Prompt
beschreibt, bis in die Reihenfolge hinein:

    Eingabe pruefen → eigene Einrichtung pruefen → Bestellung anlegen und
    Verbindung schliessen → Stripe rufen → Verbindung erneut oeffnen,
    Sitzungskennung nachtragen

Entscheidung David: den vorhandenen Weg ausbauen. Die **Regeln** stehen
deshalb hier, an einer Stelle; der Endpunkt darueber ist duenn.

**Der Preis kommt nie aus der Anfrage.** ORDERS_03 nennt das
sicherheitskritisch, und zu Recht: Wird der Betrag uebernommen, kauft jeder
das Workbook fuer einen Cent. Er kommt aus `products` — und `_betraege`
rechnet ihn aus dem **Bruttopreis**, weil `price_brutto` seit dem 21.08. der
Endpreis ist (L-61).

**Der Riegel fuer Verbraucher.** Ohne Widerrufsverzicht darf ein digitales
Produkt nicht sofort ausgeliefert werden (§ 356 Abs. 5 BGB). Die vollstaendige
rechtliche Umsetzung kommt in ORDERS_05; die Sperre steht schon hier, damit
sie nicht vergessen wird — der Prompt sagt das ausdruecklich, und ein
Verkauf ohne Widerrufsbelehrung laesst die Frist **nie** ablaufen.
"""
import logging
import re
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, text

logger = logging.getLogger(__name__)

#: Bestellnummern digitaler Produkte. Das Buch hat `HS-`; ein eigener
#: Praefix haelt beides in **einer** Tabelle auseinander, ohne dass jemand
#: eine Spalte lesen muss, um zu wissen, worum es geht.
PRAEFIX = "B"

#: Absichtlich streng genug, um Tippfehler zu fangen, und weit genug, um
#: keine gueltige Adresse abzulehnen. Wer hier zu streng prueft, verliert
#: Kunden an eine Regex.
_MAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def bestellnummer(db, jahr: int) -> str:
    """Die naechste Nummer des Jahres — `B-2026-0001`.

    **Aus der Datenbank gezaehlt, nicht mitgeschrieben** — dieselbe
    Begruendung wie bei `buch_preise.bestellnummer`: Ein Zaehler im Speicher
    springt beim Neustart zurueck und vergibt bei zwei Instanzen dieselbe
    Nummer zweimal. Die Eindeutigkeit sichert der Index, nicht diese
    Funktion.
    """
    from modelle_buch import BookOrder

    praefix = f"{PRAEFIX}-{jahr}-"
    hoechste = (db.query(func.max(BookOrder.order_number))
                  .filter(BookOrder.order_number.like(f"{praefix}%"))
                  .scalar())
    laufend = 0
    if hoechste:
        try:
            laufend = int(str(hoechste).rsplit("-", 1)[-1])
        except ValueError:
            laufend = 0
    return f"{praefix}{laufend + 1:04d}"


def produkt_holen(db, slug: str):
    """Die Katalogzeile — oder 404.

    Nur `live`. Ein Entwurf ist kein Angebot: Die drei digitalen Produkte
    stehen bis ORDERS_05 bewusst auf `draft`, und bis dahin muss auch ein
    von Hand zusammengebauter Aufruf an ihnen scheitern. Ein Riegel, den nur
    die Oberflaeche kennt, ist keiner.
    """
    zeile = db.execute(text(
        "SELECT * FROM products WHERE slug = :s AND status = 'live'"
    ), {"s": (slug or "").strip()}).mappings().first()
    if not zeile:
        raise HTTPException(404, "Dieses Produkt gibt es nicht oder es ist "
                                 "derzeit nicht bestellbar")
    return zeile


def eingabe_pruefen(daten: dict) -> None:
    """Was fehlen darf und was nicht.

    **Zuerst die Eingabe, dann die eigene Einrichtung** — wie in
    `routers/buch.py`. Umgekehrt bekaeme jemand, der den Verzicht vergisst,
    ein „nicht eingerichtet" zu lesen: eine Auskunft ueber uns statt ueber
    seine Eingabe.
    """
    mail = (daten.get("buyer_email") or "").strip()
    if not _MAIL.match(mail):
        raise HTTPException(400, "Bitte eine gueltige E-Mail-Adresse angeben")
    if not (daten.get("buyer_name") or "").strip():
        raise HTTPException(400, "Bitte einen Namen angeben")
    if not (daten.get("buyer_address") or "").strip():
        raise HTTPException(400, "Bitte eine Anschrift angeben")
    if not daten.get("terms_accepted"):
        raise HTTPException(400, "Bitte die AGB akzeptieren")

    # **Der Riegel.** Siehe Kopftext: Ohne Verzicht keine sofortige
    # Auslieferung an einen Verbraucher.
    if not daten.get("is_business") and not daten.get("withdrawal_waived"):
        raise HTTPException(
            400,
            "Fuer die sofortige Bereitstellung brauchen wir Ihre "
            "Zustimmung, dass Sie damit Ihr Widerrufsrecht verlieren. "
            "Ohne diese Zustimmung koennen wir nicht sofort ausliefern.")


def frist_bis(produkt, heute: date = None) -> date:
    """Bis wann sich der Betrag anrechnen laesst — oder `None`.

    **`None` ist eine Aussage.** Ein Produkt, das nicht anrechenbar ist,
    bekommt kein Datum statt eines erfundenen: Eine Frist, die niemand
    zugesagt hat, ist eine Zusage.

    Monatsarithmetik ohne Fremdbibliothek: Der Tag bleibt, der Monat waechst.
    Faellt der Tag im Zielmonat aus (31. August plus sechs Monate waere der
    31. Februar), zieht die Schleife zurueck auf den letzten gueltigen — das
    ist die uebliche Lesart einer Monatsfrist und wirft keinen Fehler.
    """
    monate = int(produkt.get("credit_months") or 0)
    if not produkt.get("is_creditable") or monate <= 0:
        return None

    heute = heute or date.today()
    jahr, monat = heute.year, heute.month + monate
    jahr, monat = jahr + (monat - 1) // 12, (monat - 1) % 12 + 1
    tag = heute.day
    while tag > 0:
        try:
            return date(jahr, monat, tag)
        except ValueError:
            tag -= 1
    return None


def _betraege(produkt) -> tuple:
    """Brutto und Steuersatz in Cent — **aus dem Katalog**, nie aus der Anfrage."""
    brutto_cents = int(round(float(produkt["price_brutto"]) * 100))
    return brutto_cents, float(produkt["tax_rate"])


def anlegen(db, daten: dict, produkt):
    """Die Bestellung mit Status `created`. Gibt den Eintrag zurueck."""
    from modelle_buch import BookOrder

    brutto_cents, steuer = _betraege(produkt)

    gueltig_bis = frist_bis(produkt)

    name = (daten.get("buyer_name") or "").strip()
    teile = name.split(" ", 1)

    eintrag = BookOrder(
        order_number=bestellnummer(db, datetime.utcnow().year),
        # `variant` gehoert dem Buch; fuer Katalogprodukte steht die Kennung
        # in `product_slug`. Die Spalte ist `nullable=False`, deshalb ein
        # sprechender Wert statt einer leeren Zeichenkette.
        variant="katalog",
        product_slug=produkt["slug"],
        book_version="",
        email=(daten.get("buyer_email") or "").strip().lower(),
        first_name=teile[0],
        last_name=teile[1] if len(teile) > 1 else "",
        company=(daten.get("buyer_company") or "").strip(),
        ship_street=(daten.get("buyer_address") or "").strip()[:200],
        price_gross_cents=brutto_cents,
        tax_rate=steuer,
        shipping_cents=0,
        payment_status="created",
        is_business=bool(daten.get("is_business")),
        buyer_vat_id=(daten.get("buyer_vat_id") or "").strip()[:50],
        credit_valid_until=gueltig_bis,
        # **Der Zeitstempel ist der Nachweis, nicht das Haeckchen allein.**
        # Uebernommen aus `modelle_buch`; im Streitfall zaehlt, wann
        # zugestimmt wurde.
        waiver_accepted=bool(daten.get("withdrawal_waived")),
        waiver_accepted_at=(datetime.utcnow()
                            if daten.get("withdrawal_waived") else None),
    )
    db.add(eintrag)
    db.commit()
    db.refresh(eintrag)
    logger.info("Bestellung %s angelegt: %s, %d Cent",
                eintrag.order_number, produkt["slug"], brutto_cents)
    return eintrag
