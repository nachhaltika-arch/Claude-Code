"""
Ein Schalter, der allen automatischen Mailversand anhaelt.

**Warum es ihn gibt.** Am 17.08.2026 verschickte ein taeglicher Job vier
Monate lang Erinnerungen an Firmen, die nie Kunde waren. Als es auffiel, gab
es keinen Weg, ihn anzuhalten: kein Schalter in der Oberflaeche, kein
Endpunkt, nichts. Es blieb ein Eingriff in die Datenbank oder ein Deploy —
Minuten bis Stunden, und beides kann nicht jeder. Der Schalter hat gefehlt,
also gibt es ihn jetzt.

**Er steht auf „aus", solange nichts anderes dasteht.** Ein System, in dem
niemand ausdruecklich „ja, versende automatisch" gesagt hat, versendet nicht.
Nach diesem Vorfall ist das die Richtung, in die ein Fehler fallen soll. Und
weil ein stiller Aus-Zustand seine eigene Falle waere, zeigt die Oberflaeche
ihn im Menue an, nicht nur in den Einstellungen.

**Er gilt nur fuer Maschinenpost.** Wer sein Passwort zuruecksetzt oder im
Widget eine Bestaetigung anfordert, hat gefragt — diese Mails haengen nicht an
diesem Schalter. Gesperrt wird, was ohne menschlichen Anlass rausgeht:
Scheduler-Jobs, E-Mail-Strecken, Ueberwachungsberichte.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

#: Schluessel in `system_settings`.
EINSTELLUNG = "automatischer_versand"

_AN = frozenset({"true", "1", "an", "ja", "on", "yes"})
_AUS = frozenset({"false", "0", "aus", "nein", "off", "no"})


def _lesen(db) -> Optional[str]:
    from database import SystemSettings

    zeile = db.query(SystemSettings).filter(SystemSettings.key == EINSTELLUNG).first()
    return zeile.value if zeile else None


def automatischer_versand_erlaubt(db) -> bool:
    """Darf ein Job gerade von sich aus eine Mail verschicken?

    Gibt im Zweifel ``False`` zurueck — ohne Sitzung, ohne Eintrag, bei einem
    unlesbaren Wert und auch dann, wenn die Abfrage scheitert. Eine Sperre,
    die bei einem Fehler oeffnet, ist keine.
    """
    if db is None:
        return False

    try:
        wert = _lesen(db)
    except Exception as fehler:  # noqa: BLE001 — im Zweifel gesperrt
        logger.warning(f"Versandsperre nicht lesbar, bleibt gesperrt: {fehler}")
        return False

    if wert is None:
        return False

    normiert = str(wert).strip().lower()
    if normiert in _AN:
        return True
    if normiert in _AUS:
        return False

    logger.warning(
        f"Versandsperre: {wert!r} ist weder an noch aus — bleibt gesperrt"
    )
    return False


def setzen(db, erlaubt: bool, admin_id: Optional[int] = None) -> None:
    """Schaltet den automatischen Versand an oder aus."""
    roh_setzen(db, "true" if erlaubt else "false", admin_id=admin_id)
    logger.warning(
        "Automatischer Mailversand wurde %s (Admin %s)",
        "EINGESCHALTET" if erlaubt else "ABGESCHALTET",
        admin_id if admin_id is not None else "unbekannt",
    )


def roh_setzen(db, wert, admin_id: Optional[int] = None) -> None:
    """Schreibt den Wert unveraendert. Fuer Tests und Migrationen."""
    from database import SystemSettings

    zeile = db.query(SystemSettings).filter(SystemSettings.key == EINSTELLUNG).first()
    if zeile:
        zeile.value = wert
        if admin_id is not None:
            zeile.updated_by = admin_id
    else:
        db.add(SystemSettings(key=EINSTELLUNG, value=wert, updated_by=admin_id))
    db.commit()


def zuruecksetzen(db) -> None:
    """Entfernt den Eintrag — danach gilt wieder „aus"."""
    from database import SystemSettings

    db.query(SystemSettings).filter(SystemSettings.key == EINSTELLUNG).delete()
    db.commit()


def in_eigener_sitzung_erlaubt() -> bool:
    """Wie ``automatischer_versand_erlaubt``, oeffnet aber selbst eine Sitzung.

    Fuer Aufrufer tief in Hintergrundjobs, die keine Sitzung durchgereicht
    bekommen — etwa der gemeinsame Versandhelfer des Schedulers.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        return automatischer_versand_erlaubt(db)
    except Exception as fehler:  # noqa: BLE001 — im Zweifel gesperrt
        logger.warning(f"Versandsperre nicht pruefbar, bleibt gesperrt: {fehler}")
        return False
    finally:
        db.close()
