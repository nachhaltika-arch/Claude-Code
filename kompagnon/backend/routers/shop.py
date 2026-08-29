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
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
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

    # **Die AGB-Fassung vor dem Stripe-Schluessel** (ORDERS_05, 29.08.2026).
    # `anlegen` verlangt sie ohnehin — aber erst weiter unten, und bis dahin
    # haette der Stripe-Riegel schon „Der Verkauf ist noch nicht eingerichtet"
    # geantwortet. Dieselbe Meldung fuer zwei verschiedene Ursachen schickt
    # jemanden auf die Suche nach einem Schluessel, der laengst da ist.
    #
    # **Hier und nicht weiter oben:** Erst die Eingabe, dann die eigene
    # Einrichtung — die Regel des Kopftextes gilt auch fuer das Produkt. Ein
    # Entwurf ist nicht bestellbar (404), und diese Auskunft gehoert dem
    # Aufrufer, nicht unsere Einrichtungsfrage. Beide Reihenfolgen hat jeweils
    # eine vorhandene Zusicherung erzwungen, keine Ueberlegung.
    from services import agb

    agb.verlangen()

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


# ═══════════════════════════════════════════════════════════════════
# Zahlungsrückmeldung (ORDERS_04)
# ═══════════════════════════════════════════════════════════════════
#
# **Warum nicht die Erfolgsseite den Status setzt.** Ihre Adresse steht im
# Browser des Käufers; wer sie ohne Zahlung aufruft, bekäme sonst die Ware.
# Belastbar ist allein die Meldung von Stripe.
#
# **Eigenes Signaturgeheimnis** (L-138, 27.08.2026). Ein neuer Stripe-Endpunkt
# bekommt ein eigenes Secret — das des Buchs prüft die Signatur dieser Adresse
# nicht, und ein geteiltes Geheimnis hebt die Trennung der Wege wieder auf.


def _geheimnis() -> str:
    """Bei jedem Aufruf gelesen, nicht beim Import.

    Ein Modulwert wird beim ersten Import eingefroren; wer die Variable auf
    Render nachträgt, müsste den Dienst neu starten, ohne zu wissen warum.
    """
    return os.getenv("SHOP_STRIPE_WEBHOOK_SECRET", "").strip()


def _ereignis_pruefen(rumpf: bytes, signatur: str):
    """Signatur prüfen und das Ereignis als gewöhnliche Daten zurückgeben.

    Eigene Funktion, damit die Prüfungen des Verbuchens sie ersetzen können,
    ohne eine echte Stripe-Signatur zu fälschen — und damit die Umwandlung
    aus `services/stripe_ereignis` **eine** Stelle hat (L-140: ein
    `StripeObject` ist seit stripe 15 kein `dict` mehr).
    """
    from services.stripe_ereignis import als_dict

    ereignis = stripe.Webhook.construct_event(rumpf, signatur, _geheimnis())
    return als_dict(ereignis)


def _verbuchen(sitzung: dict) -> None:
    """Eine bezahlte Shop-Bestellung auf `paid` setzen. Wirft nie."""
    from modelle_buch import BookOrder
    from services.zahlungsweg import SHOP, gehoert_hierher

    # Jeder Stripe-Endpunkt bekommt **jede** Kasse des Kontos, nicht nur die
    # eigene (services/zahlungsweg.py). Ohne diese Weiche verbuchte der Shop
    # Buch- und Websprint-Käufe mit.
    if not gehoert_hierher(SHOP, sitzung.get("metadata")):
        return

    nummer = str((sitzung.get("metadata") or {}).get("order_number") or "")
    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == nummer).first()
        if not eintrag:
            logger.error("Shop-Webhook ohne Bestellung: %r (Sitzung %s)",
                         nummer, sitzung.get("id", "?"))
            return

        # Stripe stellt bei Zweifeln erneut zu. Ohne diese Prüfung entstünden
        # doppelte Rechnung und doppelte Mail.
        if eintrag.payment_status == "paid":
            return

        # **Abweichender Betrag wird nicht verbucht, sondern gemeldet.** Ein
        # anderer Betrag als bestellt ist eine Auffälligkeit, kein Kauf — und
        # sie stillschweigend zu übernehmen hiesse, den Preis doch wieder aus
        # der Anfrage zu nehmen.
        gezahlt = sitzung.get("amount_total")
        if gezahlt is not None and int(gezahlt) != int(eintrag.price_gross_cents):
            logger.error("Shop %s: gezahlt %s Cent, bestellt %s Cent — nicht "
                         "verbucht", nummer, gezahlt, eintrag.price_gross_cents)
            return

        eintrag.payment_status = "paid"
        eintrag.stripe_payment_intent = str(sitzung.get("payment_intent") or "")
        db.commit()
    except Exception as fehler:                          # noqa: BLE001
        logger.exception("Shop-Zahlung %s nicht verbucht: %s", nummer, fehler)
        return
    finally:
        db.close()

    _auslieferung_anstossen(nummer)


def _auslieferung_anstossen(order_number: str) -> None:
    """Stumpf für ORDERS_06 — mit Protokolleintrag, nicht leer.

    Genau hier ist in diesem Projekt fünfmal etwas gebaut und nie
    angeschlossen worden. Ein sichtbarer Eintrag zeigt beim ersten echten Kauf,
    dass die Stelle erreicht wird — und dass sie noch nichts tut.
    """
    logger.info("Auslieferung für %s steht aus — ORDERS_06 ist noch nicht "
                "gebaut", order_number)


@router.post("/webhook")
async def webhook(request: Request, hintergrund: BackgroundTasks):
    """Nimmt die Zahlungsmeldung von Stripe entgegen.

    **Immer HTTP 200, außer bei ungültiger Signatur.** Ein Fehlercode
    veranlasst Stripe, denselben Vorgang über Tage erneut zu senden; der
    Fehler gehört ins Protokoll, nicht in die Antwort.

    **Der Rohkörper, nicht ein geparstes Modell.** Die Signaturprüfung rechnet
    über die Bytes, die Stripe gesendet hat — jede Umformung davor lässt sie
    scheitern, mit einer Meldung, die nicht darauf hindeutet.
    """
    rumpf = await request.body()
    signatur = request.headers.get("stripe-signature", "")

    if not _geheimnis():
        # 400 und nicht 200: Eine nicht eingerichtete Adresse soll auffallen,
        # statt jede Meldung stillschweigend zu schlucken.
        logger.error("SHOP_STRIPE_WEBHOOK_SECRET fehlt — Meldung verworfen")
        raise HTTPException(400, "Webhook nicht eingerichtet")

    try:
        ereignis = _ereignis_pruefen(rumpf, signatur)
    except (ValueError, stripe.error.SignatureVerificationError) as fehler:
        logger.error("Ungueltige Stripe-Signatur am Shop-Webhook: %s", fehler)
        raise HTTPException(400, "Ungueltige Signatur")

    if ereignis.get("type") == "checkout.session.completed":
        sitzung = (ereignis.get("data") or {}).get("object") or {}
        hintergrund.add_task(_verbuchen, sitzung)

    return {"received": True}


@router.get("/orders/{order_number}/status")
def bestellstatus(order_number: str):
    """Was die Danke-Seite fragen darf — und sonst nichts.

    **Keine personenbezogenen Daten, keine Beträge, keine Anschrift.** Die
    Bestellnummer steht im Browserverlauf und in E-Mails; sie ist kein
    Geheimnis. Wer hier den vollen Datensatz ausliefert, baut eine
    Datenschutzlücke in eine öffentliche Route.
    """
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == order_number).first()
        if not eintrag:
            raise HTTPException(404, "Bestellung nicht gefunden")
        return {
            "order_number": eintrag.order_number,
            "status": eintrag.payment_status,
            "product_code": eintrag.product_slug or "",
        }
    finally:
        db.close()
