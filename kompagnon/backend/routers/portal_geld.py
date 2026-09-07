# -*- coding: utf-8 -*-
"""Rechnungen, Zahlungsart und Einzug.

**Am 07.09.2026 aus `routers/portal.py` herausgeloest (L-25).** Die Datei war
auf 1.630 Zeilen gewachsen — doppelt ueber der Grenze —, und der groesste Teil
dieses Wachstums stammt aus den Sitzungen vom 06. und 07.09.: Kundenkonto,
Mitwirkung, Dazubuchen, Zugaenge. Geschnitten ist nach **Zustaendigkeit**,
nicht nach Groesse; das ist dasselbe Vorgehen wie bei `academy.py` am 23.08.

Der Router traegt denselben Praefix wie das Hauptmodul. Die Routen bleiben
Pfad fuer Pfad dieselben — gegengeprueft mit einer Zaehlung vor und nach dem
Schnitt.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db, Lead
from routers.auth_router import get_current_user
from routers.portal_basis import (
    verlangt_geldblick,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portal", tags=["portal"])


@router.get("/zahlungen")
def get_zahlungen(user=Depends(verlangt_geldblick), db: Session = Depends(get_db)):
    """Abos, Rechnungen und der Zustand des Zahlungskontos."""
    from services import abo_vertrag, zahlungsportal

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        return {"abos": [], "rechnungen": [], "zahlungskonto": "kein_betrieb"}

    from services import abo_stunden

    # **Der Kunde sieht, was er zahlt und wie es eingezogen wird.** Bis zum
    # 04.09.2026 stand hier nur Produkt und Zeitraum — ein Abo ohne Betrag
    # ist genau die Leerstelle aus L-160.
    abos = [{"produkt": v.produkt, "start_monat": v.start_monat,
             "end_monat": v.end_monat, "notiz": v.notiz or "",
             "abrechnung": v.abrechnung,
             "einzug_eingerichtet": bool(v.stripe_subscription_id),
             # **Netto, Steuersatz und brutto — alle drei** (Entscheidung
             # David, 04.09.2026: die Abo-Preise sind netto gemeint). Der
             # Betrieb hat „149 € netto" unterschrieben und bekommt 177,31 €
             # abgebucht. Nur eine der beiden Zahlen zu zeigen erzeugt den
             # Anruf, der mit „bei mir steht aber etwas anderes" beginnt.
             "brutto_cent": abo_stunden.preis_brutto_cent(v.produkt),
             "netto_cent": abo_stunden.preis_netto_cent(v.produkt),
             "steuersatz": abo_stunden.STEUERSATZ_ABO,
             "laeuft": v.end_monat is None}
            for v in abo_vertrag.vertraege(db, lead.id)]

    # Rechnungen ueber die Mailadresse — derselbe Weg wie `/api/invoices/my`.
    # Zwei Wege zu denselben Zeilen laufen auseinander.
    zeilen = db.execute(text(
        "SELECT invoice_number, amount_gross, status, due_date, paid_at, created_at, "
        "line_item FROM invoices WHERE customer_email = :mail "
        "ORDER BY created_at DESC LIMIT 24"), {"mail": user.email}).fetchall()
    rechnungen = [dict(r._mapping) for r in zeilen]

    # **Der Zustand des Zahlungskontos, nicht ein Ja/Nein.** „Kein Konto" und
    # „Stripe nicht eingerichtet" sind zwei verschiedene Lagen: die eine
    # betrifft den Kunden, die andere uns.
    try:
        zustand = "vorhanden" if zahlungsportal.kundenkennung(db, lead) else "keins"
    except zahlungsportal.StripeNichtEingerichtet:
        zustand = "dienst_fehlt"

    return {"abos": abos, "rechnungen": rechnungen, "zahlungskonto": zustand}


class PortalZiel(BaseModel):
    rueckkehr: str = ""


@router.post("/zahlungen/verwalten")
def zahlungen_verwalten(body: PortalZiel, user=Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Eine Sitzung im Billing-Portal — die Adresse gilt einmal und kurz."""
    from services import zahlungsportal
    from services.base_urls import public_base_url

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        raise HTTPException(404, "Kein Betrieb gefunden")

    # Die Rueckkehradresse kommt aus der Umgebung, nicht aus dem Rumpf: Ein
    # mitgeschickter Wert waere eine offene Weiterleitung.
    ziel = f"{public_base_url()}/app/portal"
    try:
        return {"url": zahlungsportal.portal_sitzung(db, lead, ziel)}
    except zahlungsportal.KeinZahlungskonto as fehler:
        raise HTTPException(409, str(fehler))
    except zahlungsportal.StripeNichtEingerichtet:
        raise HTTPException(503, "Der Zahlungsdienst ist gerade nicht erreichbar.")


@router.post("/zahlungen/einzug")
def zahlungen_einzug(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Den Einzug für das laufende Pflege-Abo einrichten (Entscheidung 04.09.2026).

    **Warum das der Kunde selbst tut.** Eine Einzugsermächtigung ist seine
    Zustimmung; sie lässt sich nicht im Innendienst setzen. Der Vertrag steht
    schon — hier wird nur der Weg eröffnet, auf dem Stripe die Erlaubnis
    einholt und das Abonnement startet.

    **Ein Vertrag auf `rechnung` bekommt hier nichts.** Er ist unter anderen
    Bedingungen geschlossen worden, und der Aufstellungslauf berechnet ihn.
    Ihm hier stillschweigend eine Abbuchung anzubieten hieße, die Bedingung
    zu wechseln, ohne dass jemand zustimmt.
    """
    from services import abo_stripe, abo_vertrag, zahlungsportal
    from services.base_urls import public_base_url

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        raise HTTPException(404, "Kein Betrieb gefunden")

    vertrag = abo_vertrag.laufender(db, lead.id)
    if vertrag is None:
        raise HTTPException(409, "Für Ihren Betrieb läuft kein Pflege-Abo.")
    if vertrag.abrechnung != "stripe":
        raise HTTPException(
            409, "Dieses Abo wird per Rechnung abgerechnet. Wenn Sie auf "
                 "Lastschrift wechseln möchten, sagen Sie uns kurz Bescheid.")
    if vertrag.stripe_subscription_id:
        raise HTTPException(409, "Der Einzug ist für dieses Abo bereits eingerichtet.")

    try:
        kennung = zahlungsportal.kundenkennung(db, lead) or ""
    except zahlungsportal.StripeNichtEingerichtet:
        raise HTTPException(503, "Der Zahlungsdienst ist gerade nicht erreichbar.")

    ziel = f"{public_base_url()}/app/portal"
    try:
        return abo_stripe.kaufweg(
            vertrag.produkt, lead_id=lead.id, email=user.email or "",
            betrieb=lead.company_name or "",
            erfolg_url=f"{ziel}?einzug=eingerichtet",
            abbruch_url=f"{ziel}?einzug=abgebrochen",
            kennung_kunde=kennung)
    except abo_stripe.StripeNichtEingerichtet:
        raise HTTPException(503, "Der Zahlungsdienst ist gerade nicht erreichbar.")
    except abo_stripe.UnbekanntesAbo as fehler:
        raise HTTPException(500, str(fehler))
