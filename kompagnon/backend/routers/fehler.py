"""Was der Server nicht verarbeiten konnte — abrufbar, statt nur im Log.

Luecke L-10. Ins Serverlog sieht niemand taeglich; deshalb stand der 500er
beim Anlegen einer Lektion monatelang unbemerkt (18.08.2026). Diese Liste ist
die Gegenmassnahme: kurz, zusammengefasst, nach Haeufigkeit sortierbar.

Nur fuer den Innendienst — in Meldungen und Spuren koennen Kundendaten stehen.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import Fehlerprotokoll, get_db
from routers.auth_router import require_innendienst

router = APIRouter(prefix="/api/fehler", tags=["fehler"],
                   dependencies=[Depends(require_innendienst)])


def _als_dict(e: Fehlerprotokoll, mit_spur: bool = False) -> dict:
    daten = {
        "id": e.id,
        "art": e.art,
        "pfad": e.pfad,
        "methode": e.methode,
        "meldung": e.meldung,
        "anzahl": e.anzahl,
        "zuerst": e.zuerst.isoformat() if e.zuerst else None,
        "zuletzt": e.zuletzt.isoformat() if e.zuletzt else None,
    }
    if mit_spur:
        daten["spur"] = e.spur
    return daten


@router.get("/")
def liste(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Die zuletzt aufgetretenen Fehler, gleiche zusammengefasst."""
    eintraege = (db.query(Fehlerprotokoll)
                   .order_by(Fehlerprotokoll.zuletzt.desc())
                   .limit(limit)
                   .all())

    seit = datetime.utcnow() - timedelta(hours=24)
    return {
        "gesamt": db.query(Fehlerprotokoll).count(),
        # Die Zahl, die zaehlt: Was ist *heute* passiert. Ein Protokoll, das
        # nur Gesamtsummen zeigt, sieht immer gleich schlimm aus.
        "letzte_24h": (db.query(Fehlerprotokoll)
                         .filter(Fehlerprotokoll.zuletzt >= seit)
                         .count()),
        "eintraege": [_als_dict(e) for e in eintraege],
    }


@router.get("/{fehler_id}")
def einzeln(fehler_id: int, db: Session = Depends(get_db)):
    """Ein Eintrag samt Spur — die steht nicht in der Liste, damit die Liste
    lesbar bleibt."""
    eintrag = db.query(Fehlerprotokoll).filter(Fehlerprotokoll.id == fehler_id).first()
    if not eintrag:
        raise HTTPException(404, "Kein solcher Eintrag")
    return _als_dict(eintrag, mit_spur=True)
