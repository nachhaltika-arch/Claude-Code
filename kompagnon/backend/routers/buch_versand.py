# -*- coding: utf-8 -*-
"""Die Warteschlange der Druckbestellungen (BUCH-07, L-115).

**Der Befund.** `fulfillment_status` wurde beim Bestellen auf `queued` gesetzt
und danach von niemandem gelesen. Es gab keine Ansicht, keinen Export und
keinen Weg, eine Sendungsnummer einzutragen; `fulfillment_exported_at` und
`tracking_number` waren Spalten, die nie jemand beschrieb. Ein Kaeufer haette
gezahlt, und sein Buch stuende in einer Zeile, die kein Mensch aufschlaegt —
dieselbe Klasse, die diesen Bestand fuenfmal getroffen hat.

**Es gibt keine BoD-Schnittstelle, und hier entsteht auch keine.** BoD und
epubli bieten keine oeffentliche Bestell-API. Gebaut wird deshalb genau das,
was ohne eine solche funktioniert: eine interne Liste mit CSV-Ausgabe, die
David einmal in der Woche oeffnet, bei BoD als Direktbestellung aufgibt und
mit Sendungsnummern zurueckschreibt. Eine „Automatik", die im Betrieb still
fehlschlaegt, waere schlechter als die Handarbeit.

**Der Export mutiert, also ist er ein POST.** Der Auftrag sah ein `GET` vor.
Ein `GET`, das Bestellungen auf `exported` setzt, wird von einem Vorauslader,
einem Doppelklick oder einem Neuladen ausgeloest — und dann ist die
Warteschlange leer, ohne dass jemand die Datei gesehen hat. Es kostet auch
nichts: Der Endpunkt verlangt einen Anmeldekopf, den ein `<a href>` ohnehin
nicht mitschicken kann; die Oberflaeche muss die Datei so oder so abrufen und
selbst zum Herunterladen anbieten.
"""
import csv
import io
import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from modelle_buch import BookOrder
from routers.auth_router import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/book", tags=["book"])

#: Bezahlt und wartet auf den Druck.
WARTEND = "queued"
#: In eine CSV geschrieben und bei BoD aufgegeben.
EXPORTIERT = "exported"
#: Unterwegs, Sendungsnummer vorhanden.
VERSENDET = "shipped"

#: Was von Hand gesetzt werden darf. `awaiting_payment` steht bewusst **nicht**
#: darin: Es beschreibt eine Tatsache aus Stripe, keine Entscheidung des
#: Innendienstes. Wer eine unbezahlte Bestellung auf `queued` heben koennte,
#: haette genau den Weg zurueck, den `services/buch_warteschlange` schliesst.
SETZBAR = (WARTEND, EXPORTIERT, VERSENDET)

#: Nur bezahlte Bestellungen werden gedruckt. Der Status ist eine Behauptung,
#: `payment_status` die Tatsache — und zwei Bedingungen, die dasselbe sagen
#: sollen, sind billiger als der Tag, an dem eine von beiden nicht stimmt.
BEZAHLT = "paid"


# ═══════════════════════════════════════════════════════════════════
# Schemata — die Feldnamen hier sind die, die das Frontend liest
# ═══════════════════════════════════════════════════════════════════

class BestellungFuerDenInnendienst(BaseModel):
    """Eine Zeile der Liste. Ohne Zahlungsnummern und ohne Abruf-Token."""

    id: int
    order_number: str
    variant: str
    created_at: Optional[datetime]
    first_name: str
    last_name: str
    company: str
    email: str
    ship_street: str
    ship_zip: str
    ship_city: str
    ship_country: str
    payment_status: str
    fulfillment_status: str
    fulfillment_exported_at: Optional[datetime]
    tracking_number: str
    price_gross_cents: int
    shipping_cents: int


class Warteschlange(BaseModel):
    """Die Liste samt der vier Zahlen darueber."""

    bestellungen: list[BestellungFuerDenInnendienst]
    gesamt: int
    offen: int
    exportiert: int
    versendet: int
    #: Bezahlter Bruttoumsatz des laufenden Kalendermonats, in Cent.
    umsatz_monat_cents: int


class VersandAenderung(BaseModel):
    fulfillment_status: str
    tracking_number: str = Field(default="", max_length=100)


# ═══════════════════════════════════════════════════════════════════
# Lesen
# ═══════════════════════════════════════════════════════════════════

def _grundmenge(db: Session):
    """Alles, was ueberhaupt eine Abwicklung hat — Druck und Buendel.

    Katalogbestellungen aus dem Shop tragen `not_applicable` und gehoeren
    nicht hierher; sie werden als Datei ausgeliefert.
    """
    return db.query(BookOrder).filter(
        BookOrder.fulfillment_status.isnot(None),
        BookOrder.fulfillment_status != "not_applicable",
    )


def _monatsumsatz_cents(db: Session) -> int:
    heute = date.today()
    beginn = datetime(heute.year, heute.month, 1)
    zeilen = db.query(BookOrder).filter(
        BookOrder.payment_status == BEZAHLT,
        BookOrder.created_at >= beginn,
    ).all()
    return sum((z.price_gross_cents or 0) + (z.shipping_cents or 0) for z in zeilen)


@router.get("/orders", response_model=Warteschlange)
def bestellungen_lesen(
    status: Optional[str] = None,
    variant: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Die Druckbestellungen, neueste zuerst.

    **Die vier Zahlen zaehlen die ganze Warteschlange, nicht die Seite.** Wer
    filtert, will trotzdem wissen, wie viele Buecher insgesamt zu drucken
    sind — eine Kennzahl, die sich mit dem Filter aendert, beantwortet die
    Frage „was muss diese Woche raus" nicht mehr.
    """
    alle = _grundmenge(db)

    gefiltert = alle
    if status:
        gefiltert = gefiltert.filter(BookOrder.fulfillment_status == status)
    if variant:
        gefiltert = gefiltert.filter(BookOrder.variant == variant)
    if from_date:
        gefiltert = gefiltert.filter(BookOrder.created_at >= datetime.combine(
            from_date, datetime.min.time()))
    if to_date:
        gefiltert = gefiltert.filter(BookOrder.created_at <= datetime.combine(
            to_date, datetime.max.time()))

    zeilen = (gefiltert.order_by(BookOrder.created_at.desc())
              .offset(offset).limit(limit).all())

    def zaehle(wert: str) -> int:
        return _grundmenge(db).filter(
            BookOrder.fulfillment_status == wert,
            BookOrder.payment_status == BEZAHLT,
        ).count()

    return Warteschlange(
        bestellungen=[BestellungFuerDenInnendienst(
            id=z.id,
            order_number=z.order_number,
            variant=z.variant,
            created_at=z.created_at,
            first_name=z.first_name or "",
            last_name=z.last_name or "",
            company=z.company or "",
            email=z.email or "",
            ship_street=z.ship_street or "",
            ship_zip=z.ship_zip or "",
            ship_city=z.ship_city or "",
            ship_country=z.ship_country or "",
            payment_status=z.payment_status or "",
            fulfillment_status=z.fulfillment_status or "",
            fulfillment_exported_at=z.fulfillment_exported_at,
            tracking_number=z.tracking_number or "",
            price_gross_cents=z.price_gross_cents or 0,
            shipping_cents=z.shipping_cents or 0,
        ) for z in zeilen],
        gesamt=gefiltert.count(),
        offen=zaehle(WARTEND),
        exportiert=zaehle(EXPORTIERT),
        versendet=zaehle(VERSENDET),
        umsatz_monat_cents=_monatsumsatz_cents(db),
    )


# ═══════════════════════════════════════════════════════════════════
# Export
# ═══════════════════════════════════════════════════════════════════

#: Die Spalten in genau dieser Reihenfolge (BUCH-07).
SPALTEN = ["Bestellnummer", "Anrede", "Vorname", "Nachname", "Firma",
           "Strasse", "PLZ", "Ort", "Land", "Menge", "Variante", "Bestelldatum"]

#: **`Anrede` bleibt leer, und das ist keine Luecke in dieser Datei.** Die
#: Kasse fragt sie nicht ab; es gibt keine Spalte dafuer. Die Ueberschrift
#: steht trotzdem, weil das Formular bei BoD sie kennt — wer sie fuellen will,
#: erhebt sie zuerst beim Kauf.
#:
#: **`Menge` ist immer 1**, weil eine Bestellung genau ein Buch ist:
#: `routers/buch.py` uebergibt Stripe fest `"quantity": 1`. Fuenf Exemplare
#: fuer ein Team waeren heute fuenf Bestellungen. Die Spalte steht als Zahl
#: und nicht als Leerfeld, damit die Summe im Tabellenblatt stimmt.
MENGE_JE_BESTELLUNG = 1


@router.post("/orders/export")
def csv_export(
    status: str = Query(default=WARTEND),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Eine CSV fuer die Direktbestellung bei BoD — und die Zeilen sind danach
    als exportiert vermerkt.

    **`utf-8-sig`, also mit Byte-Order-Mark.** Ohne sie zerlegt Excel jeden
    Umlaut; dasselbe Muster steht in `routers/leads_import.py`.

    **Bezahlt wird zweimal geprueft.** Bis zum 01.09.2026 setzte
    `routers/buch.py` `fulfillment_status='queued'` bereits beim **Anlegen**
    der Bestellung — vor der Zahlung. Eine abgebrochene Kasse stand damit in
    der Warteschlange, und wer diese Datei bei BoD aufgab, druckte und
    verschickte ein Buch, das niemand bezahlt hat. Die Ursache ist behoben
    (`awaiting_payment` bis Stripe bestaetigt); die Bedingung hier bleibt,
    weil aeltere Zeilen den falschen Status noch tragen koennen.
    """
    if status not in SETZBAR:
        raise HTTPException(422, f"Unbekannter Status: {status}")

    zeilen = (_grundmenge(db)
              .filter(BookOrder.fulfillment_status == status,
                      BookOrder.payment_status == BEZAHLT)
              .order_by(BookOrder.created_at.asc()).all())

    puffer = io.StringIO()
    schreiber = csv.writer(puffer, delimiter=";")
    schreiber.writerow(SPALTEN)
    for z in zeilen:
        schreiber.writerow([
            z.order_number,
            "",                                     # Anrede — nie erhoben
            z.first_name or "",
            z.last_name or "",
            z.company or "",
            z.ship_street or "",
            z.ship_zip or "",
            z.ship_city or "",
            z.ship_country or "DE",
            MENGE_JE_BESTELLUNG,
            z.variant or "",
            z.created_at.strftime("%Y-%m-%d") if z.created_at else "",
        ])

    jetzt = datetime.utcnow()
    for z in zeilen:
        z.fulfillment_status = EXPORTIERT
        z.fulfillment_exported_at = jetzt
    db.commit()

    logger.info("BoD-Export: %d Bestellungen aus %r nach %r", len(zeilen),
                status, EXPORTIERT)

    name = f"bod-bestellungen-{jetzt.strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([puffer.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


# ═══════════════════════════════════════════════════════════════════
# Zurueckschreiben
# ═══════════════════════════════════════════════════════════════════

def _versandmail(eintrag: BookOrder) -> bool:
    """Die Versandbestaetigung. Wirft nie.

    **Eine gescheiterte Mail nimmt den Versandvermerk nicht mit** — dieselbe
    Regel wie in `routers/shop.py`: Der Vermerk ist die Hauptsache, die Mail
    das Beiwerk. Waere es umgekehrt, stuende die Bestellung nach einem
    Mailfehler weiter als „exportiert" in der Liste, und beim naechsten
    Export ginge sie ein zweites Mal an BoD.
    """
    from services.email import send_email

    sendung = (f"<p>Ihre Sendungsnummer: <b>{eintrag.tracking_number}</b></p>"
               if eintrag.tracking_number else "")
    html = (f"<p>Ihr Buch zur Bestellung {eintrag.order_number} ist unterwegs.</p>"
            f"{sendung}"
            f"<p>Die Zustellung dauert ueblicherweise wenige Werktage.</p>")
    try:
        return bool(send_email(
            eintrag.email,
            f"Ihr Buch ist unterwegs - Bestellnr. {eintrag.order_number}",
            html))
    except Exception:
        logger.exception("Versandbestaetigung fuer %s fehlgeschlagen",
                         eintrag.order_number)
        return False


@router.patch("/orders/{order_id}/fulfillment")
def versand_setzen(
    order_id: int,
    aenderung: VersandAenderung,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Status und Sendungsnummer einer Druckbestellung.

    **Die Mail geht nur beim Uebergang.** Wer eine Sendungsnummer korrigiert,
    loest keine zweite Benachrichtigung aus; sonst bekaeme der Kaeufer bei
    jedem Tippfehler eine weitere Mail.
    """
    if aenderung.fulfillment_status not in SETZBAR:
        raise HTTPException(
            422, "Erlaubt sind: " + ", ".join(SETZBAR))

    eintrag = db.query(BookOrder).filter(BookOrder.id == order_id).first()
    if not eintrag:
        raise HTTPException(404, "Bestellung nicht gefunden")
    if eintrag.fulfillment_status in (None, "", "not_applicable"):
        # Eine Datei hat keinen Versand. Das stillschweigend zuzulassen
        # ergaebe eine Zeile, die in der Warteschlange auftaucht, obwohl es
        # nichts zu drucken gibt.
        raise HTTPException(422, "Diese Bestellung hat keine Druckabwicklung")

    vorher = eintrag.fulfillment_status
    eintrag.fulfillment_status = aenderung.fulfillment_status
    if aenderung.tracking_number:
        eintrag.tracking_number = aenderung.tracking_number.strip()[:100]
    db.commit()
    db.refresh(eintrag)

    benachrichtigt = False
    if aenderung.fulfillment_status == VERSENDET and vorher != VERSENDET:
        benachrichtigt = _versandmail(eintrag)

    return {
        "id": eintrag.id,
        "fulfillment_status": eintrag.fulfillment_status,
        "tracking_number": eintrag.tracking_number or "",
        "benachrichtigt": benachrichtigt,
    }
