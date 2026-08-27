# -*- coding: utf-8 -*-
"""Der Bezahlvorgang für digitale Produkte (L-100, ORDERS_03).

**Dünn mit Absicht.** Die Regeln stehen in `services/bestellung.py`, der
Ablauf folgt `routers/buch.py` — Entscheidung David: den vorhandenen Weg
ausbauen statt eine vierte Kasse zu erfinden. Hier steht nur, was ein
Endpunkt tun muss: entgegennehmen, weiterreichen, antworten.

**Die Reihenfolge ist nicht beliebig.** Sie steht so in ORDERS_03 und hat in
`buch.py` denselben Grund:

1. Eingabe prüfen — vor der eigenen Einrichtung, sonst liest jemand, der ein
   Häkchen vergaß, eine Auskunft über *uns*.
2. Bestellung anlegen, **Verbindung schließen**. Der Stripe-Aufruf dauert
   ein bis mehrere Sekunden; bliebe die Verbindung offen, wären die
   Verbindungen der Datenbank bei gleichzeitigen Käufern schnell erschöpft.
3. Stripe rufen — **in einem Thread**. `stripe.checkout.Session.create` ist
   synchron; direkt in einer `async def` aufgerufen legt sie die
   Ereignisschleife still, und der Render-Proxy antwortet mit 503. Zwölf
   solcher Stellen sind am 18.08. behoben worden; das hier wird nicht die
   dreizehnte.
4. Verbindung erneut öffnen, Sitzungskennung nachtragen.
"""
import logging
import os

import anyio
import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import SessionLocal
from services import bestellung as best

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/shop", tags=["shop"])


class Kaufanfrage(BaseModel):
    product_code: str
    buyer_email: str
    buyer_name: str
    buyer_address: str
    buyer_company: str = ""
    buyer_vat_id: str = ""
    is_business: bool = False
    terms_accepted: bool = False
    withdrawal_waived: bool = False


def _frontend_adresse() -> str:
    """Wohin Stripe zurückleitet.

    Aus der Umgebung, nicht fest eingetragen: Staging und Produktiv haben
    verschiedene Adressen, und ein fester Wert schickt den Käufer der
    Staging-Probe in die Produktivumgebung.
    """
    return (os.getenv("FRONTEND_URL", "").strip().rstrip("/")
            or "https://kas.kompagnon.group")


@router.post("/checkout")
async def kasse(anfrage: Kaufanfrage):
    """Bestellung anlegen und die Adresse der Stripe-Kasse liefern."""
    daten = anfrage.model_dump()

    # ── 1. Eingabe, dann eigene Einrichtung ──────────────────
    best.eingabe_pruefen(daten)

    db = SessionLocal()
    try:
        produkt = best.produkt_holen(db, anfrage.product_code)
    finally:
        db.close()

    if not (os.getenv("STRIPE_SECRET_KEY", "").strip()):
        # 503, nicht 500: Das ist ein Einrichtungszustand, kein Fehler — und
        # die Meldung sagt es, statt „Interner Serverfehler" zu behaupten.
        raise HTTPException(503, "Der Verkauf ist noch nicht eingerichtet")
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()

    # ── 2. Anlegen, Verbindung schliessen ────────────────────
    db = SessionLocal()
    try:
        eintrag = best.anlegen(db, daten, produkt)
        nummer = eintrag.order_number
        betrag = eintrag.price_gross_cents
        name = produkt["name"]
    finally:
        db.close()

    # ── 3. Stripe — im Thread ────────────────────────────────
    basis = _frontend_adresse()
    try:
        sitzung = await anyio.to_thread.run_sync(
            lambda: stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "quantity": 1,
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": betrag,
                        "product_data": {"name": name},
                    },
                }],
                customer_email=anfrage.buyer_email.strip(),
                locale="de",
                metadata={
                    "order_number": nummer,
                    "product_code": produkt["slug"],
                },
                success_url=f"{basis}/shop/danke?order={nummer}",
                cancel_url=f"{basis}/shop?abgebrochen=1",
            ))
    except stripe.error.StripeError as fehler:
        logger.error("Stripe lehnte die Kasse fuer %s ab: %s", nummer, fehler)
        raise HTTPException(400, "Die Zahlung konnte nicht eroeffnet werden")

    # ── 4. Kennung nachtragen ────────────────────────────────
    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == nummer).first()
        if eintrag:
            eintrag.stripe_session_id = sitzung.id
            db.commit()
    finally:
        db.close()

    return {"order_number": nummer, "checkout_url": sitzung.url}
