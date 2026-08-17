"""
Der Not-Aus fuer automatischen Mailversand.

Am 17.08.2026 lief ein Job vier Monate lang taeglich gegen Fremdadressen. Es
gab keinen Weg, ihn anzuhalten, ausser einem Deploy oder einem Eingriff in die
Datenbank — beides dauert, und beides kann nicht jeder. Diese Sperre ist der
Schalter, der gefehlt hat.

Zwei Entscheidungen sind hier festgehalten und werden geprueft:

**Erstens: aus, solange nichts anderes dasteht.** Ist die Einstellung nicht
gesetzt, gilt sie als *gesperrt*. Wer automatisch versenden will, sagt es
ausdruecklich. Nach dem Vorfall ist das die richtige Richtung — ein frisch
aufgesetztes System verschickt nichts, bevor jemand hinsieht.

**Zweitens: sie gilt nur fuer Maschinenpost.** Wer sein Passwort zuruecksetzt
oder im Widget eine Bestaetigung anfordert, hat gefragt. Diese Mails duerfen
nie an einem Schalter haengen, den jemand vergessen hat.
"""
import pytest

from services import versandsperre


@pytest.fixture
def db(app):
    """Eine Sitzung gegen die Testdatenbank. `app` legt das Schema an."""
    from database import SessionLocal

    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


# ── Grundverhalten ─────────────────────────────────────────────────────

def test_ohne_einstellung_ist_der_versand_gesperrt(db):
    versandsperre.zuruecksetzen(db)

    assert versandsperre.automatischer_versand_erlaubt(db) is False


def test_einschalten_erlaubt_den_versand(db):
    versandsperre.setzen(db, True)

    assert versandsperre.automatischer_versand_erlaubt(db) is True


def test_ausschalten_sperrt_wieder(db):
    versandsperre.setzen(db, True)
    versandsperre.setzen(db, False)

    assert versandsperre.automatischer_versand_erlaubt(db) is False


def test_der_zustand_ueberdauert_die_abfrage(db):
    versandsperre.setzen(db, True)

    assert versandsperre.automatischer_versand_erlaubt(db) is True
    assert versandsperre.automatischer_versand_erlaubt(db) is True


# ── Unlesbare Werte ────────────────────────────────────────────────────

@pytest.mark.parametrize("wert", ["", "vielleicht", "1.5", "ja bitte", None])
def test_ein_unlesbarer_wert_sperrt(db, wert):
    # Ein kaputter Eintrag darf nicht versehentlich freischalten. Im Zweifel
    # geht nichts raus — das ist die Richtung, in die ein Fehler fallen soll.
    versandsperre.roh_setzen(db, wert)

    assert versandsperre.automatischer_versand_erlaubt(db) is False


@pytest.mark.parametrize("wert", ["true", "True", "TRUE", "1", "an", "ja"])
def test_uebliche_schreibweisen_fuer_an(db, wert):
    versandsperre.roh_setzen(db, wert)

    assert versandsperre.automatischer_versand_erlaubt(db) is True


@pytest.mark.parametrize("wert", ["false", "False", "0", "aus", "nein"])
def test_uebliche_schreibweisen_fuer_aus(db, wert):
    versandsperre.roh_setzen(db, wert)

    assert versandsperre.automatischer_versand_erlaubt(db) is False


# ── Ohne Datenbank ─────────────────────────────────────────────────────

def test_ohne_sitzung_gilt_gesperrt():
    # Aufrufer aus Hintergrundjobs haben nicht immer eine Sitzung zur Hand.
    # Auch dann darf nicht einfach gesendet werden.
    assert versandsperre.automatischer_versand_erlaubt(None) is False
