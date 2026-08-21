"""Fehler festhalten, ohne dabei selbst zu stoeren.

Siehe `database.Fehlerprotokoll` fuer das Warum. Hier stehen die drei Regeln,
die dieses Modul gegenueber jedem anderen unterscheiden:

1. **Es darf nie etwas mitreissen.** Wenn das Festhalten scheitert, ist das
   aergerlich — die Anfrage daran sterben zu lassen, waere schlimmer.
2. **Es fasst zusammen.** Gleiche Art an gleicher Stelle zaehlt hoch.
3. **Es speichert wenig.** Die Spur gekuerzt, keinen Anfragerumpf. In einem
   Traceback koennen Kundendaten stehen.
"""
import hashlib
import logging
from datetime import datetime, timedelta

from database import Fehlerprotokoll, SessionLocal

logger = logging.getLogger(__name__)

#: So viel Spur wird aufbewahrt. Genug fuer die Stelle, zu wenig fuer einen
#: Datensatz.
SPUR_MAX = 2000

#: Danach wird aufgeraeumt. Was aelter ist, hat niemanden mehr interessiert.
AUFBEWAHRUNG_TAGE = 30


def _kennung(art: str, pfad: str, spur: str) -> str:
    """Gleiche Art, gleiche Stelle, gleicher erster Spurschritt = ein Eintrag."""
    erste_zeile = (spur or "").strip().splitlines()[-1:] or [""]
    roh = f"{art}|{pfad}|{erste_zeile[0]}"
    return hashlib.sha1(roh.encode("utf-8", "replace")).hexdigest()[:32]


def merke_fehler(pfad, methode, art, meldung, spur="", benutzer_id=None):
    """Haelt einen Fehler fest. Gibt den Eintrag zurueck — oder `None`, wenn
    selbst das nicht ging."""
    try:
        db = SessionLocal()
    except Exception as fehler:            # pragma: no cover — siehe Regel 1
        logger.error("Fehlerprotokoll nicht erreichbar: %s", fehler)
        return None

    try:
        kennung = _kennung(art, pfad, spur)
        jetzt = datetime.utcnow()
        eintrag = (db.query(Fehlerprotokoll)
                     .filter(Fehlerprotokoll.kennung == kennung)
                     .first())

        if eintrag:
            eintrag.anzahl = (eintrag.anzahl or 1) + 1
            eintrag.zuletzt = jetzt
            eintrag.meldung = (meldung or "")[:1000]
        else:
            eintrag = Fehlerprotokoll(
                kennung=kennung,
                art=(art or "")[:120],
                pfad=(pfad or "")[:500],
                methode=(methode or "")[:10],
                meldung=(meldung or "")[:1000],
                spur=(spur or "")[:SPUR_MAX],
                benutzer_id=benutzer_id,
                anzahl=1,
                zuerst=jetzt,
                zuletzt=jetzt,
            )
            db.add(eintrag)

        db.commit()
        db.refresh(eintrag)
        return eintrag
    except Exception as fehler:
        logger.error("Fehler liess sich nicht festhalten: %s", fehler)
        try:
            db.rollback()
        except Exception:
            pass
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass


def alte_aufraeumen(tage: int = AUFBEWAHRUNG_TAGE) -> int:
    """Entfernt, was laenger nicht mehr aufgetreten ist. Gibt die Zahl zurueck."""
    grenze = datetime.utcnow() - timedelta(days=tage)
    db = SessionLocal()
    try:
        entfernt = (db.query(Fehlerprotokoll)
                      .filter(Fehlerprotokoll.zuletzt < grenze)
                      .delete(synchronize_session=False))
        db.commit()
        return entfernt
    except Exception as fehler:            # pragma: no cover
        logger.error("Aufraeumen fehlgeschlagen: %s", fehler)
        db.rollback()
        return 0
    finally:
        db.close()
