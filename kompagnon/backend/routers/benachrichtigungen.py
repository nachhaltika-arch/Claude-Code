# -*- coding: utf-8 -*-
"""Der Posteingang des Innendienstes (L-18).

**Warum die Sperre am Router hängt und nicht an jeder Route.** Diese Zeilen
tragen Betriebsnamen, Betreffzeilen und Ausschnitte aus dem, was Kunden
schreiben. Am 19.08. entstanden 55 offene Routen dadurch, dass der Schutz an
jeder einzelnen hing und eine vergessen wurde (L-51). Eine Vorgabe am Router
kann man nicht vergessen.

**Gelöscht wird nichts.** Wer versehentlich auf „gelesen" klickt, soll die
Meldung wiederfinden — sie steht weiter in der Liste, nur nicht mehr fett.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import Benachrichtigung, get_db
from routers.auth_router import require_innendienst

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benachrichtigungen", tags=["benachrichtigungen"],
                   dependencies=[Depends(require_innendienst)])

#: Wie viele die Liste höchstens zeigt. Die Glocke ist kein Archiv; wer
#: weiter zurück will, findet den Vorgang dort, wo er hingehört —
#: am Betrieb oder im Ticketbildschirm.
HOECHSTENS = 100


def _auskunft(z: Benachrichtigung) -> dict:
    return {
        "id": z.id,
        "art": z.art,
        "lead_id": z.lead_id,
        "titel": z.titel,
        "hinweis": z.hinweis or "",
        "ziel": z.ziel or "",
        "erstellt_am": z.erstellt_am.isoformat() if z.erstellt_am else None,
        "gelesen": z.gelesen_am is not None,
    }


@router.get("")
def auflisten(nur_ungelesen: bool = Query(False),
              db: Session = Depends(get_db)):
    """Die neuesten zuerst — das ist die, die jemand lesen will."""
    abfrage = db.query(Benachrichtigung)
    if nur_ungelesen:
        abfrage = abfrage.filter(Benachrichtigung.gelesen_am.is_(None))

    zeilen = (abfrage.order_by(Benachrichtigung.id.desc())
              .limit(HOECHSTENS).all())
    return [_auskunft(z) for z in zeilen]


@router.get("/anzahl")
def anzahl(db: Session = Depends(get_db)):
    """Nur die Zahl — die Glocke im Kopf braucht keine Liste.

    Getrennt, weil sie oft geholt wird und die Liste selten.
    """
    offen = (db.query(Benachrichtigung)
             .filter(Benachrichtigung.gelesen_am.is_(None)).count())
    return {"ungelesen": offen}


@router.post("/{kennung}/gelesen")
def gelesen(kennung: int, db: Session = Depends(get_db)):
    zeile = db.query(Benachrichtigung).filter(
        Benachrichtigung.id == kennung).first()
    if not zeile:
        raise HTTPException(404, "Benachrichtigung nicht gefunden")

    if zeile.gelesen_am is None:
        zeile.gelesen_am = datetime.utcnow()
        db.commit()
    return _auskunft(zeile)


@router.post("/alle-gelesen")
def alle_gelesen(db: Session = Depends(get_db)):
    """Der Knopf für den Morgen nach dem Urlaub."""
    anzahl_offen = (db.query(Benachrichtigung)
                    .filter(Benachrichtigung.gelesen_am.is_(None))
                    .update({Benachrichtigung.gelesen_am: datetime.utcnow()},
                            synchronize_session=False))
    db.commit()
    return {"gelesen": anzahl_offen}
