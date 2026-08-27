# -*- coding: utf-8 -*-
"""Verkauf des Buchs „Der Homepage Standard" (BUCH-05).

Drei Endpunkte: die Kasse, der Webhook von Stripe und eine magere Auskunft für
die Danke-Seite.

**Was hier bewusst anders ist als in `routers/payments.py`:**

* **Kein zweiter Stripe-Client.** Schlüssel und Muster kommen aus demselben
  Modul; hier steht nur, was das Buch anders macht.
* **Die Stripe-Aufrufe laufen über `asyncio.to_thread`.** Die Bibliothek
  arbeitet synchron; direkt in einer `async def` aufgerufen hielte sie die
  Ereignisschleife an — genau der Fehler, der am 18.08.2026 an zwölf Stellen
  zu „Verbindungsfehler" in der Oberfläche führte.
* **Die Datenbanksitzung ist zu, während Stripe antwortet.** Ein Netzaufruf
  von einer halben Sekunde, der eine Verbindung aus dem Vorrat festhält,
  erschöpft ihn unter Last.
"""
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

import anyio
import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from modelle_buch import BookOrder
from services import buch_preise

logger = logging.getLogger(__name__)

#: Dasselbe Muster wie in `routers/widget.py`.
EMAIL_MUSTER = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$")

router = APIRouter(prefix="/api/book", tags=["book"])

#: Wohin Stripe den Käufer zurückschickt. Ohne diese Adresse landet er nach
#: der Zahlung auf einer Seite, die es nicht gibt.
FRONTEND_BOOK_URL = os.getenv("FRONTEND_BOOK_URL", "").rstrip("/")
#: Der in Stripe angelegte Steuersatz von sieben Prozent. `automatic_tax`
#: bleibt aus: Stripe würde sonst 19 % ansetzen, weil es das Buch nicht kennt.
STRIPE_TAX_RATE_ID_7 = os.getenv("STRIPE_TAX_RATE_ID_7", "")
#: Das Signaturgeheimnis **dieses** Endpunkts.
#:
#: **Jede in Stripe eingetragene Adresse hat ihr eigenes.** Bis zum
#: 27.08.2026 stand hier `STRIPE_WEBHOOK_SECRET` — dasselbe, das
#: `routers/payments.py` liest. Sobald `/api/book/webhook` als zweite Adresse
#: eingetragen wird, prüft diese Zeile jede Meldung gegen das Geheimnis der
#: **falschen** Adresse: Die Signatur schlägt fehl, der Endpunkt antwortet
#: mit 400, Stripe wiederholt tagelang, und keine einzige Buchbestellung
#: würde je auf „bezahlt" gesetzt.
#:
#: Der Rückfall auf den alten Namen ist Absicht: Solange nur **eine** Adresse
#: eingetragen ist, bleibt die bisherige Einrichtung gültig.
WEBHOOK_SECRET = (os.getenv("STRIPE_WEBHOOK_SECRET_BUCH")
                  or os.getenv("STRIPE_WEBHOOK_SECRET", ""))

#: Wie lange ein Abruflink gilt. Lang genug für einen Urlaub, kurz genug,
#: dass ein weitergereichter Link nicht ewig trägt.
ABRUF_TAGE = 30


def konfiguration_pruefen() -> list:
    """Was fehlt, damit ein Buch verkauft werden kann — beim Start gemeldet.

    Stillschweigend weiterzulaufen wäre das Schlechteste: Die Kasse sähe
    funktionsfähig aus und schlüge erst beim ersten Käufer fehl.
    """
    fehlt = []
    if not os.getenv("STRIPE_SECRET_KEY"):
        fehlt.append("STRIPE_SECRET_KEY")
    if not WEBHOOK_SECRET:
        fehlt.append("STRIPE_WEBHOOK_SECRET_BUCH")
    if not FRONTEND_BOOK_URL:
        fehlt.append("FRONTEND_BOOK_URL")
    if not STRIPE_TAX_RATE_ID_7:
        fehlt.append("STRIPE_TAX_RATE_ID_7")
    if fehlt:
        logger.warning(
            "Buchverkauf unvollständig eingerichtet — fehlt: %s. "
            "Die Kasse antwortet bis dahin mit 503.", ", ".join(fehlt))
    return fehlt


konfiguration_pruefen()


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class BuchBestellung(BaseModel):
    """Was der Käufer im Formular angibt."""

    variant: str
    email: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    ship_street: str = ""
    ship_zip: str = ""
    ship_city: str = ""
    ship_country: str = "DE"
    waiver_accepted: bool = False
    utm_source: str = ""
    utm_campaign: str = ""

    @field_validator("email")
    @classmethod
    def _adresse_pruefen(cls, wert: str) -> str:
        """Dasselbe Muster wie im Widget — keine neue Abhängigkeit dafür.

        `EmailStr` von Pydantic verlangt das Paket `email-validator`, das im
        Backend nicht liegt. Eine Abhängigkeit für ein Feld aufzunehmen, das
        das Widget seit Monaten mit einem Ausdruck prüft, wäre die teurere
        Lösung — und zwei Prüfungen für dieselbe Sache die schlechtere.
        """
        wert = (wert or "").strip()
        if not EMAIL_MUSTER.match(wert):
            raise ValueError("Bitte eine gültige E-Mail-Adresse angeben")
        return wert

    @field_validator("variant")
    @classmethod
    def _variante_kennen(cls, wert: str) -> str:
        if wert not in buch_preise.VARIANTEN:
            raise ValueError(
                "Unbekannte Ausgabe. Möglich sind: "
                + ", ".join(buch_preise.VARIANTEN))
        return wert


class BestellAuskunft(BaseModel):
    """Was die Danke-Seite erfährt — und mehr nicht.

    Diese Auskunft ist **öffentlich**: Wer eine Bestellnummer kennt, bekommt
    sie. Deshalb keine Anschrift, kein Abruftoken, und die Adresse nur
    verkürzt.
    """

    order_number: str
    variant: str
    payment_status: str
    email_masked: str


def _maskieren(email: str) -> str:
    name, _, domain = (email or "").partition("@")
    if not domain:
        return ""
    sichtbar = name[:2] if len(name) > 2 else name[:1]
    return f"{sichtbar}{'*' * max(3, len(name) - len(sichtbar))}@{domain}"


# ═══════════════════════════════════════════════════════════════════
# Kasse
# ═══════════════════════════════════════════════════════════════════

def _pruefe_bestellung(bestellung: BuchBestellung) -> dict:
    """Fachliche Prüfungen, die kein Schema abnimmt."""
    variante = buch_preise.variante(bestellung.variant)

    if bestellung.variant in ("print", "bundle"):
        fehlend = [name for name, wert in (
            ("Straße", bestellung.ship_street),
            ("Postleitzahl", bestellung.ship_zip),
            ("Ort", bestellung.ship_city)) if not wert.strip()]
        if fehlend:
            raise HTTPException(
                422, "Für die gedruckte Ausgabe fehlt die Lieferanschrift: "
                     + ", ".join(fehlend))

    if bestellung.variant in ("pdf", "bundle") and not bestellung.waiver_accepted:
        # § 356 Abs. 5 BGB: Ohne diese Zustimmung bleibt das Widerrufsrecht
        # bestehen — bei einer Datei, die der Käufer sofort bekommt.
        raise HTTPException(
            422, "Zustimmung zum sofortigen Beginn der Lieferung erforderlich")

    return variante


def _bestellung_anlegen(db: Session, bestellung: BuchBestellung,
                        variante: dict) -> BookOrder:
    jetzt = datetime.utcnow()
    for versuch in range(5):
        nummer = buch_preise.bestellnummer(db, jetzt.year)
        eintrag = BookOrder(
            order_number=nummer,
            variant=bestellung.variant,
            book_version=buch_preise.BUCH_FASSUNG,
            email=str(bestellung.email),
            first_name=bestellung.first_name.strip(),
            last_name=bestellung.last_name.strip(),
            company=bestellung.company.strip(),
            ship_street=bestellung.ship_street.strip(),
            ship_zip=bestellung.ship_zip.strip(),
            ship_city=bestellung.ship_city.strip(),
            ship_country=(bestellung.ship_country or "DE").upper()[:2],
            price_gross_cents=variante["brutto_cents"],
            tax_rate=buch_preise.STEUERSATZ,
            shipping_cents=variante["versand_cents"],
            payment_status="pending",
            waiver_accepted=bestellung.waiver_accepted,
            waiver_accepted_at=jetzt if bestellung.waiver_accepted else None,
            fulfillment_status=("queued" if bestellung.variant in ("print", "bundle")
                                else "not_applicable"),
            utm_source=bestellung.utm_source[:100],
            utm_campaign=bestellung.utm_campaign[:100],
        )
        db.add(eintrag)
        try:
            db.commit()
            db.refresh(eintrag)
            return eintrag
        except Exception:
            # Zwei gleichzeitige Bestellungen können dieselbe Nummer errechnen.
            # Der eindeutige Index fängt es; hier wird schlicht neu gezählt.
            db.rollback()
            if versuch == 4:
                raise
    raise HTTPException(500, "Bestellnummer konnte nicht vergeben werden")


def _stripe_positionen(variante: dict, bestellung: BuchBestellung) -> list:
    steuer = [STRIPE_TAX_RATE_ID_7] if STRIPE_TAX_RATE_ID_7 else None
    positionen = [{
        "price_data": {
            "currency": "eur",
            "product_data": {"name": variante["bezeichnung"]},
            "unit_amount": variante["brutto_cents"],
        },
        "quantity": 1,
    }]
    if variante["versand_cents"]:
        positionen.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Versand innerhalb Deutschlands"},
                "unit_amount": variante["versand_cents"],
            },
            "quantity": 1,
        })
    if steuer:
        for position in positionen:
            position["tax_rates"] = steuer
    return positionen


@router.post("/checkout")
async def kasse(bestellung: BuchBestellung):
    """Legt die Bestellung an und liefert die Adresse der Stripe-Kasse."""
    # **Erst die Bestellung prüfen, dann die eigene Einrichtung.** Umgekehrt
    # bekäme jemand, der die Zustimmung zum Widerruf vergisst, ein „nicht
    # eingerichtet" zu lesen — eine Auskunft über uns statt über seine Eingabe.
    variante = _pruefe_bestellung(bestellung)

    fehlt = konfiguration_pruefen()
    if "STRIPE_SECRET_KEY" in fehlt or "FRONTEND_BOOK_URL" in fehlt:
        raise HTTPException(503, "Der Buchverkauf ist noch nicht eingerichtet")

    # Erste Sitzung: anlegen, dann schließen.
    db = SessionLocal()
    try:
        eintrag = _bestellung_anlegen(db, bestellung, variante)
        nummer = eintrag.order_number
    finally:
        db.close()

    try:
        sitzung = await anyio.to_thread.run_sync(lambda: stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=_stripe_positionen(variante, bestellung),
            customer_email=str(bestellung.email),
            locale="de",
            metadata={
                "order_number": nummer,
                "variant": bestellung.variant,
                "book_version": buch_preise.BUCH_FASSUNG,
            },
            success_url=f"{FRONTEND_BOOK_URL}/danke?order={nummer}",
            cancel_url=f"{FRONTEND_BOOK_URL}/?abgebrochen=1",
        ))
    except stripe.error.StripeError as fehler:
        logger.error("Stripe lehnte die Kasse für %s ab: %s", nummer, fehler)
        raise HTTPException(400, "Die Zahlung konnte nicht eröffnet werden")

    # Zweite Sitzung: Kennung nachtragen.
    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == nummer).first()
        if eintrag:
            eintrag.stripe_session_id = sitzung.id
            db.commit()
    finally:
        db.close()

    return {"checkout_url": sitzung.url, "order_number": nummer}


# ═══════════════════════════════════════════════════════════════════
# Webhook
# ═══════════════════════════════════════════════════════════════════

def _lead_verknuepfen(db: Session, eintrag: BookOrder) -> None:
    """Den Käufer in die Pipeline holen — vorhandenen Betrieb oder neuen Lead.

    Ohne diesen Schritt verkauft das System Bücher und verliert die Käufer.
    """
    from database import Lead

    vorhanden = db.query(Lead).filter(Lead.email == eintrag.email).first()
    if vorhanden:
        eintrag.lead_id = vorhanden.id
        return
    name = " ".join(t for t in (eintrag.first_name, eintrag.last_name) if t)
    lead = Lead(
        company_name=eintrag.company or name or eintrag.email,
        email=eintrag.email,
        lead_source="buch",
    )
    db.add(lead)
    db.flush()
    eintrag.lead_id = lead.id


def auslieferung_anstossen(order_number: str) -> None:
    """Platzhalter für BUCH-06.

    **Bewusst ein Stumpf mit Protokolleintrag, keine leere Funktion.** Genau
    hier ist in diesem Projekt fünfmal etwas gebaut und nie angeschlossen
    worden; ein sichtbarer Eintrag im Protokoll zeigt beim ersten echten Kauf,
    dass die Stelle erreicht wird — und dass sie noch nichts tut.
    """
    logger.info("Auslieferung für %s steht aus — BUCH-06 ist noch nicht gebaut",
                order_number)


def _zahlung_verbuchen(sitzung: dict) -> None:
    # **Auch hier kommt jede Kasse des Kontos an**, nicht nur die des Buchs
    # und des Shops (siehe `services/zahlungsweg.py`). Ohne diese Weiche
    # meldete der Eintrag unten bei **jedem** Websprint-Kauf einen Fehler —
    # ein Protokoll voller Fehlalarme ist eines, in dem der echte Fehler
    # untergeht.
    from services.zahlungsweg import BUCH, weg_der_sitzung

    weg = weg_der_sitzung(sitzung.get("metadata"))
    if weg != BUCH:
        logger.info("Buch: Sitzung %s gehoert zum Weg %r — hier uebersprungen",
                    sitzung.get("id", "?"), weg)
        return

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.stripe_session_id == sitzung.get("id")).first()
        if not eintrag:
            logger.error("Webhook ohne Bestellung: Sitzung %s", sitzung.get("id"))
            return
        if eintrag.payment_status == "paid":
            return                      # Stripe sendet mehrfach.

        eintrag.payment_status = "paid"
        eintrag.stripe_payment_intent = str(sitzung.get("payment_intent") or "")
        if eintrag.ist_digital:
            eintrag.download_token = secrets.token_urlsafe(32)[:64]
            eintrag.download_expires_at = datetime.utcnow() + timedelta(days=ABRUF_TAGE)
        if eintrag.braucht_anschrift:
            eintrag.fulfillment_status = "queued"
        _lead_verknuepfen(db, eintrag)
        db.commit()
        nummer = eintrag.order_number
    finally:
        db.close()
    auslieferung_anstossen(nummer)


@router.post("/webhook")
async def webhook(request: Request, hintergrund: BackgroundTasks):
    """Nimmt die Zahlungsmeldung von Stripe entgegen.

    **Antwortet auch bei internen Fehlern mit 200.** Ein Fehlercode brächte
    Stripe dazu, denselben Vorgang tagelang erneut zu senden. Der Fehler
    gehört ins Protokoll, nicht in die Antwort — die Signaturprüfung ist die
    einzige Ausnahme.
    """
    rumpf = await request.body()
    signatur = request.headers.get("stripe-signature")

    if not WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET fehlt — Zahlungsmeldung verworfen")
        raise HTTPException(400, "Webhook nicht eingerichtet")
    try:
        ereignis = stripe.Webhook.construct_event(rumpf, signatur, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as fehler:
        logger.error("Ungültige Stripe-Signatur: %s", fehler)
        raise HTTPException(400, "Ungültige Signatur")

    if ereignis["type"] == "checkout.session.completed":
        try:
            hintergrund.add_task(_zahlung_verbuchen, ereignis["data"]["object"])
        except Exception as fehler:                     # pragma: no cover
            logger.exception("Zahlung konnte nicht verbucht werden: %s", fehler)

    return {"received": True}


# ═══════════════════════════════════════════════════════════════════
# Auskunft für die Danke-Seite
# ═══════════════════════════════════════════════════════════════════

@router.get("/order/{order_number}", response_model=BestellAuskunft)
def bestellung_ansehen(order_number: str, db: Session = Depends(get_db)):
    eintrag = db.query(BookOrder).filter(
        BookOrder.order_number == order_number).first()
    if not eintrag:
        raise HTTPException(404, "Bestellung nicht gefunden")
    return BestellAuskunft(
        order_number=eintrag.order_number,
        variant=eintrag.variant,
        payment_status=eintrag.payment_status,
        email_masked=_maskieren(eintrag.email),
    )


@router.get("/varianten")
def varianten() -> dict:
    """Was verkauft wird — für die Landingpage, aus einer Quelle."""
    return {
        "book_version": buch_preise.BUCH_FASSUNG,
        "tax_rate": float(buch_preise.STEUERSATZ),
        "variants": {
            schluessel: {
                "label": werte["bezeichnung"],
                "gross_cents": werte["brutto_cents"],
                "shipping_cents": werte["versand_cents"],
                "total_cents": werte["brutto_cents"] + werte["versand_cents"],
            }
            for schluessel, werte in buch_preise.VARIANTEN.items()
        },
    }
