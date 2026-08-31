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
from typing import Optional

import anyio
import stripe
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from database import SessionLocal
from routers.auth_router import require_innendienst
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


#: Wie lange ein Abruf-Link gilt. Dieselbe Frist wie beim Buch — zwei
#: verschiedene Fristen fuer denselben Vorgang muesste jemand erklaeren.
ABRUF_TAGE = 30

#: Wie oft dieselbe Bestellung ihre Datei holen darf (BUCH-06, Punkt 1).
#:
#: **Der Zaehler war da und niemand las ihn** (gefunden am 31.08.2026, L-105):
#: `download_count` wurde bei jedem Abruf erhoeht und nirgends geprueft. Eine
#: Zahl, die mitlaeuft und nichts bewirkt, sieht im Datensatz aus wie eine
#: Begrenzung — und wer sie sieht, haelt die Auslieferung fuer begrenzt.
#:
#: **Fuenf und nicht eins:** Ein Kaeufer wechselt das Geraet, verliert die
#: Datei, laedt sie im Buero noch einmal. Die Grenze soll die Weitergabe an
#: Dritte unattraktiv machen, nicht den ehrlichen Fall bestrafen.
ABRUFE_HOECHSTENS = 5


def _mail_versenden(an: str, betreff: str, html: str) -> bool:
    """Der vorhandene Weg, kein dritter.

    ORDERS_06 warnt ausdruecklich davor: Es gibt bereits zwei parallele
    Mailwege. `services/email.send_email` ist der zentrale — Brevo zuerst,
    SMTP als zweiter. Eigene Funktion nur, damit die Pruefungen sie ersetzen
    koennen, ohne eine Mail zu verschicken.
    """
    from services.email import send_email

    return send_email(an, betreff, html)


def _bestaetigung_senden(eintrag) -> bool:
    """Die Bestellbestaetigung mit Abruf-Link.

    **Sie wiederholt die akzeptierten Erklaerungen** (ORDERS_05 Schritt 4):
    Fassung der AGB und der Wortlaut des Widerrufsverzichts. Im Streitfall
    zaehlt, was der Kaeufer bestaetigt bekommen hat — nicht, was in einer
    Datenbankspalte steht.

    **Der Link zeigt auf uns, nicht auf den Speicher.** Eine signierte
    R2-Adresse laege sonst monatelang im Postfach und in jedem Mailarchiv;
    dieser Link gilt dreissig Tage, die signierte Adresse entsteht erst beim
    Klick und lebt Minuten.
    """
    from services import agb

    basis = _frontend_adresse()
    abruf = f"{os.getenv('BACKEND_URL', '').strip().rstrip('/') or basis}" \
            f"/api/shop/download/{eintrag.download_token}"

    fassung = eintrag.terms_version or agb.fassung() or "—"
    html = (
        f"<p>Vielen Dank für Ihre Bestellung {eintrag.order_number}.</p>"
        f"<p><a href=\"{abruf}\">Hier können Sie Ihre Datei abrufen</a> — "
        f"der Link gilt {ABRUF_TAGE} Tage und {ABRUFE_HOECHSTENS} Abrufe.</p>"
        f"<hr><p><small>Sie haben den AGB in der Fassung {fassung} "
        f"zugestimmt.</small></p>"
    )
    if eintrag.waiver_accepted:
        html += (f"<p><small>Ihre Erklärung zur sofortigen Bereitstellung: "
                 f"{agb.verzichtstext()}</small></p>")

    # Die Rechnung haengt am selben Token wie die Datei (ORDERS_07 Schritt 4).
    rechnungslink = (f"{os.getenv('BACKEND_URL', '').strip().rstrip('/') or basis}"
                     f"/api/shop/orders/{eintrag.order_number}/invoice"
                     f"?token={eintrag.download_token}")
    html += (f'<p><a href="{rechnungslink}">Ihre Rechnung als PDF</a></p>')

    return _mail_versenden(eintrag.email,
                           f"Ihre Bestellung {eintrag.order_number}", html)


def _auslieferung_anstossen(order_number: str) -> None:
    """Abruf-Link vergeben und die Bestaetigung senden. Wirft nie.

    **Der Token wird nur einmal vergeben.** Stripe stellt bei Zweifeln erneut
    zu; ein zweiter Token machte den Link aus der ersten Mail still ungueltig,
    und der Kaeufer haette einen Link, der gestern noch ging.

    **Eine gescheiterte Mail nimmt die Auslieferung nicht mit.** Am 26.08.
    riss ein Fehler im Mailanhang den ganzen Versand mit; die Zahlung ist die
    Hauptsache, die Mail das Beiwerk. Der Token steht dann trotzdem, und der
    Innendienst kann den Link nachreichen.
    """
    import secrets
    from datetime import timedelta

    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == order_number).first()
        if not eintrag:
            logger.error("Auslieferung ohne Bestellung: %r", order_number)
            return

        if not eintrag.download_token:
            eintrag.download_token = secrets.token_urlsafe(32)[:64]
            eintrag.download_expires_at = (datetime.utcnow()
                                           + timedelta(days=ABRUF_TAGE))
        eintrag.delivered_at = eintrag.delivered_at or datetime.utcnow()
        db.commit()
        db.refresh(eintrag)
        db.expunge(eintrag)
    except Exception as fehler:                          # noqa: BLE001
        logger.exception("Auslieferung %s gescheitert: %s", order_number, fehler)
        return
    finally:
        db.close()

    # **Die Rechnung vor der Mail** (ORDERS_07): Sie gehoert in die
    # Bestaetigung, und eine Bestaetigung ohne sie muesste nachgereicht
    # werden. Scheitert sie, geht die Mail trotzdem — der Kaeufer kommt an
    # seine Datei, und die Rechnung holt der Innendienst nach.
    _rechnung_erzeugen(order_number)

    try:
        if not _bestaetigung_senden(eintrag):
            logger.error("Bestaetigung fuer %s nicht versendet — der Abruf-Link "
                         "steht, die Mail fehlt", order_number)
    except Exception as fehler:                          # noqa: BLE001
        logger.exception("Bestaetigung fuer %s gescheitert: %s",
                         order_number, fehler)


def _rechnung_erzeugen(order_number: str) -> None:
    """Die Rechnung zur bezahlten Bestellung. Wirft nie.

    Eigene Sitzung und eigener Abschluss: Der Nummernkreis haelt eine Sperre
    auf seine Zeile, bis die Transaktion schliesst (siehe
    `services/rechnungsnummer`). Sie ueber den Mailversand offen zu halten
    hiesse, den ganzen Kreis fuer die Dauer eines Brevo-Aufrufs zu blockieren.
    """
    from services import rechnung

    db = SessionLocal()
    try:
        _, grund = rechnung.fuer_bestellung(db, order_number)
        if grund:
            logger.error("Rechnung fuer %s nicht erzeugt: %s",
                         order_number, grund)
    except Exception as fehler:                          # noqa: BLE001
        logger.exception("Rechnung fuer %s gescheitert: %s",
                         order_number, fehler)
    finally:
        db.close()


@router.get("/download/{token}")
def abruf(token: str):
    """Die gekaufte Datei — als Weiterleitung auf eine kurz gueltige Adresse.

    **Unbekannt und unbezahlt sehen gleich aus.** Beide 404. Wer den
    Unterschied sehen kann, kann Bestellnummern durchprobieren und erfaehrt,
    welche es gibt.

    **Abgelaufen bekommt eine eigene Auskunft** (410): Sonst schreibt ein
    Kaeufer, dessen Frist um ist, eine Beschwerde ueber einen Link, der
    „nicht funktioniert".

    **Die Datei laeuft nicht durch uns.** R2 liefert selbst aus; ein 20-MB-PDF
    durch die Ereignisschleife zu reichen waere genau die Blockade, die am
    18.08. an zwoelf Stellen behoben wurde.
    """
    from sqlalchemy import text as sql_text

    from modelle_buch import BookOrder
    from services import produktablage

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.download_token == token).first()
        if not eintrag or eintrag.payment_status not in ("paid", "delivered"):
            raise HTTPException(404, "Abruf-Link unbekannt")

        if (eintrag.download_expires_at
                and eintrag.download_expires_at < datetime.utcnow()):
            raise HTTPException(
                410, "Dieser Abruf-Link ist abgelaufen. Bitte melden Sie sich "
                     "bei uns, wir stellen Ihnen einen neuen aus.")

        # **Aufgebraucht bekommt dieselbe Auskunft wie abgelaufen** (410, nicht
        # 403): Fuer den Kaeufer ist beides derselbe Fall — der Link geht nicht
        # mehr, und er soll sich melden. Ein „verboten" wuerde ihn wie einen
        # Eindringling behandeln, obwohl er bezahlt hat.
        if (eintrag.download_count or 0) >= ABRUFE_HOECHSTENS:
            raise HTTPException(
                410, f"Dieser Abruf-Link wurde bereits {ABRUFE_HOECHSTENS} Mal "
                     f"benutzt. Bitte melden Sie sich bei uns, wir stellen "
                     f"Ihnen einen neuen aus.")

        schluessel = db.execute(sql_text(
            "SELECT delivery_key FROM products WHERE slug = :s"),
            {"s": eintrag.product_slug}).scalar()

        fehlt = produktablage.was_fehlt()
        if fehlt or not (schluessel or "").strip():
            grund = (f"Dateiablage nicht eingerichtet: {', '.join(fehlt)}"
                     if fehlt else
                     f"Am Produkt {eintrag.product_slug!r} ist keine Datei "
                     f"hinterlegt")
            logger.error("Abruf %s nicht moeglich — %s",
                         eintrag.order_number, grund)
            raise HTTPException(
                503, "Die Datei kann gerade nicht bereitgestellt werden. "
                     "Wir kuemmern uns darum — Ihr Kauf bleibt bestehen.")

        adresse = produktablage.signierte_adresse(schluessel)
        if not adresse:
            raise HTTPException(
                503, "Die Datei kann gerade nicht bereitgestellt werden. "
                     "Wir kuemmern uns darum — Ihr Kauf bleibt bestehen.")

        # Erst zaehlen, wenn wirklich ausgeliefert wird: Ein abgelaufener oder
        # gescheiterter Versuch ist kein Abruf.
        eintrag.download_count = (eintrag.download_count or 0) + 1
        db.commit()
    finally:
        db.close()

    return RedirectResponse(adresse, status_code=307)


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


# ═══════════════════════════════════════════════════════════════════
# Anrechnung auf einen Websprint (ORDERS_08)
# ═══════════════════════════════════════════════════════════════════
#
# **Die einzige Verbindung zwischen Bestellbereich und Projekten.** Alles
# andere bleibt getrennt. Die Regeln stehen in `services/anrechnung.py`; hier
# steht nur, wer fragen darf und wie die Antwort aussieht.
#
# **Beide Routen hinter der Anmeldung.** Sie beantworten, was eine bestimmte
# Adresse gekauft hat — das ist eine Kundenauskunft, keine oeffentliche.


class Einloesung(BaseModel):
    order_number: str
    deal_id: int


@router.get("/credit-check")
def anrechnung_pruefen(email: str, fuer_deal: Optional[int] = None,
                       _=Depends(require_innendienst)):
    """Welche Anrechnungen fuer diese Adresse offen sind.

    **Alle, nicht die erste.** Jemand kann Workbook und Check PLUS gekauft
    haben — zusammen 398 EUR. Welche gezogen wird, entscheidet ein Mensch.

    **`fuer_deal` nimmt die eigene Vormerkung wieder hinein.** Wer ein Angebot
    erneut oeffnet, muss die Anrechnung sehen, die schon darin liegt — sonst
    verschwindet die Abzugsposition aus der Ansicht und jemand legt sie ein
    zweites Mal an. Fuer alle anderen Angebote bleibt sie unsichtbar.
    """
    from services import anrechnung

    db = SessionLocal()
    try:
        offene = anrechnung.offene(db, email, fuer_deal=fuer_deal)
    finally:
        db.close()

    return {
        "email": anrechnung.normalisiert(email),
        "anrechnungen": offene,
        "summe_cents": sum(e["betrag_cents"] for e in offene),
    }


@router.post("/credit-redeem")
def anrechnung_einloesen(anfrage: Einloesung, _=Depends(require_innendienst)):
    """Eine Anrechnung endgueltig auf einen Deal buchen.

    **Endgueltig ist woertlich gemeint.** Eine Ruecknahme erfolgt nur von Hand
    mit Protokolleintrag; ein Weg zurueck im Code waere ein Weg, denselben
    Betrag zweimal anzurechnen.
    """
    from services import anrechnung

    db = SessionLocal()
    try:
        eintrag, code, meldung = anrechnung.einloesen(
            db, anfrage.order_number, anfrage.deal_id)
        if code != 200:
            raise HTTPException(code, meldung)
        return {
            "order_number": eintrag.order_number,
            "deal_id": eintrag.credit_redeemed_deal_id,
            "betrag_cents": int(eintrag.price_gross_cents or 0),
            "gebucht_am": eintrag.credit_redeemed_at.isoformat(),
        }
    finally:
        db.close()


@router.get("/orders/{order_number}/invoice")
def rechnung_abrufen(order_number: str, token: str):
    """Die Rechnung — an demselben Token wie die gekaufte Datei.

    **Nicht an der Bestellnummer allein.** Die Rechnung traegt Name und
    Anschrift des Kaeufers; die Bestellnummer steht im Browserverlauf und in
    E-Mails. Sie herauszugeben, wer die Nummer kennt, waere eine
    Datenschutzluecke in einer oeffentlichen Route.
    """
    from sqlalchemy import text as sql_text

    from modelle_buch import BookOrder
    from services import produktablage, rechnung

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == order_number,
            BookOrder.download_token == token).first()
        if not eintrag or eintrag.payment_status not in ("paid", "delivered"):
            raise HTTPException(404, "Rechnung nicht gefunden")

        zeile = db.execute(sql_text(
            "SELECT invoice_number, created_at FROM invoices "
            "WHERE line_item LIKE :m ORDER BY id DESC LIMIT 1"
        ), {"m": f"%{order_number}%"}).fetchone()
        if not zeile:
            raise HTTPException(
                404, "Zu dieser Bestellung gibt es noch keine Rechnung")

        jahr = zeile[1].year if zeile[1] else None
        adresse = produktablage.signierte_adresse(
            rechnung.pfad_zu(zeile[0], jahr))
    finally:
        db.close()

    if not adresse:
        raise HTTPException(
            503, "Die Rechnung kann gerade nicht bereitgestellt werden.")
    return RedirectResponse(adresse, status_code=307)
