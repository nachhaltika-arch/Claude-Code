"""Traegt die Lebenszyklus-Phase fuer Bestandsbetriebe nach.

Die Phase entsteht ab dem 19.08.2026 von selbst — ein Ereignis in
`database.py` zieht sie mit, sobald `status` gesetzt wird. Bestandszeilen
haben nie ein `set` gesehen und stehen deshalb auf `NULL`.

Der Nachtrag rechnet sie aus, und zwar **nur** dort, wo die Phase noch leer
ist. Ein von Hand gesetzter Wert wird nicht ueberschrieben.

**Unbekannte Status bleiben leer.** Sie sollen auffallen, nicht in eine Phase
gedraengt werden — der Bericht zaehlt sie, damit jemand hinsieht.
"""
import logging
from typing import Dict

from sqlalchemy.exc import SQLAlchemyError

from database import Lead
from services.lebenszyklus import phase_zu

logger = logging.getLogger(__name__)


def phasen_nachtragen(db) -> Dict[str, int]:
    """Fuellt leere Phasen. Gibt einen Bericht zurueck."""
    bericht = {"gefuellt": 0, "ohne_zuordnung": 0}

    offen = db.query(Lead).filter(Lead.lifecycle_phase.is_(None)).all()
    if not offen:
        return bericht

    unbekannte = set()
    for betrieb in offen:
        phase = phase_zu(betrieb.status)
        if phase is None:
            bericht["ohne_zuordnung"] += 1
            if betrieb.status:
                unbekannte.add(betrieb.status)
            continue
        # Am Objekt vorbei zuweisen wuerde das Ereignis nicht ausloesen — hier
        # ist das egal, wir schreiben ja genau das Feld.
        betrieb.lifecycle_phase = phase
        bericht["gefuellt"] += 1

    if bericht["gefuellt"]:
        db.commit()

    if unbekannte:
        logger.warning(
            "Betriebe ohne zuordenbare Phase — unbekannte Status: %s",
            ", ".join(sorted(unbekannte)),
        )

    return bericht


def nachtragen_beim_start() -> None:
    """Startphase — eigene Sitzung, Bericht ins Protokoll."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        bericht = phasen_nachtragen(db)
    except SQLAlchemyError as e:  # noqa: BLE001
        db.rollback()
        logger.warning("Phasen-Nachtrag uebersprungen: %s", e)
        return
    finally:
        db.close()

    if bericht["gefuellt"] or bericht["ohne_zuordnung"]:
        logger.info(
            "✓ Lebenszyklus-Phasen nachgetragen — %d gefuellt, "
            "%d ohne Zuordnung",
            bericht["gefuellt"], bericht["ohne_zuordnung"],
        )
