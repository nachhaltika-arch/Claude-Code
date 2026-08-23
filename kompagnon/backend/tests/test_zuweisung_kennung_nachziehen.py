"""Altzeilen der Kurszuweisung tragen möglicherweise die falsche Kennung.

L-54, eröffnet am 19.08.2026: Das Kundenblatt rief
`/api/academy/customer/{id}/…` mit der **Betriebs-ID**, während die Akademie
alles andere über die **Benutzer-ID** führt. Seit demselben Tag wird beim
Schreiben aufgelöst — neue Zeilen tragen die Benutzer-ID. Die alten nicht.

Folgenlos war das, solange **niemand** die Zuweisung abfragte. Genau das hat
sich geändert; damit steht in der Tabelle möglicherweise eine Zahl, unter der
niemand sucht, und der zugewiesene Kurs bliebe für den Kunden unsichtbar.

Der Nachtrag räumt das auf — aber nur, wo er sicher ist:

- Zeile zeigt auf einen Betrieb, dessen Kunde bekannt ist, **und** es gibt
  keinen Benutzer mit derselben Nummer → umschreiben
- Beides möglich (die Zahl ist zugleich eine gültige Benutzer-ID) → **liegen
  lassen** und melden. Raten wäre hier schlimmer als nichts tun: Die zwei
  Zahlenräume laufen unabhängig, und ein falsch geratener Eintrag schaltet
  einem fremden Betrieb etwas frei
- Zeile zeigt schon auf einen Benutzer → nichts zu tun
"""
import pytest
from sqlalchemy import text

from database import (
    SessionLocal, AcademyCourse, AcademyCustomerAccess, AcademyModuleAccess,
    AcademyModule, User,
)
from services.zuweisung_kennung import kennungen_nachziehen


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture
def kurs(db):
    k = AcademyCourse(title="Nachtragprobe Kurs")
    db.add(k)
    db.commit()
    db.refresh(k)
    yield k
    db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == k.id).delete(synchronize_session=False)
    db.delete(k)
    db.commit()


@pytest.fixture
def kunde_mit_betrieb(db):
    """Ein Kunde, dessen Betriebsnummer garantiert keine Benutzernummer ist.

    Die Nummer wird bewusst hoch gesetzt: Nur so ist der Fall „eindeutig eine
    Betriebsnummer" ueberhaupt herstellbar — bei kleinen Zahlen ueberschneiden
    sich die beiden Raeume, und genau das ist der zweideutige Fall weiter unten.
    """
    from auth import hash_password

    MAIL = "nachtragprobe@kompagnon.local"

    # Reste eines abgebrochenen Laufs raeumen, sonst kollidiert die Mailadresse
    db.query(User).filter(User.email == MAIL).delete(synchronize_session=False)
    db.commit()

    hoechste = db.query(User.id).order_by(User.id.desc()).first()
    hoch = (hoechste[0] if hoechste else 0) + 5000

    db.execute(text("INSERT INTO leads (id, company_name) VALUES (:i, :n)"),
               {"i": hoch, "n": "Nachtragprobe Betrieb"})
    db.commit()

    nutzer = User(email=MAIL, password_hash=hash_password("x"), role="kunde",
                  first_name="Nach", last_name="Trag", lead_id=hoch,
                  is_active=True, is_verified=True)
    db.add(nutzer)
    db.commit()
    db.refresh(nutzer)

    yield nutzer, hoch

    db.query(User).filter(User.email == MAIL).delete(synchronize_session=False)
    db.execute(text("DELETE FROM leads WHERE id = :i"), {"i": hoch})
    db.commit()


def test_eine_betriebsnummer_wird_auf_den_benutzer_umgeschrieben(
        db, kurs, kunde_mit_betrieb):
    # Arrange
    nutzer, betrieb = kunde_mit_betrieb
    db.add(AcademyCustomerAccess(customer_id=betrieb, course_id=kurs.id))
    db.commit()

    # Act
    bericht = kennungen_nachziehen(db)

    # Assert
    zeile = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == kurs.id).first()
    assert zeile.customer_id == nutzer.id
    assert bericht["umgeschrieben"] >= 1


def test_eine_benutzernummer_bleibt_unberuehrt(db, kurs, kunde_mit_betrieb):
    # Arrange
    nutzer, _ = kunde_mit_betrieb
    db.add(AcademyCustomerAccess(customer_id=nutzer.id, course_id=kurs.id))
    db.commit()

    # Act
    kennungen_nachziehen(db)

    # Assert
    zeile = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == kurs.id).first()
    assert zeile.customer_id == nutzer.id


def test_eine_zweideutige_zahl_bleibt_liegen(db, kurs, kunde_user):
    """Wo beides möglich ist, wäre Raten schlimmer als nichts tun."""
    # Arrange — `kunde_user.id` ist zugleich eine gültige Benutzernummer
    db.add(AcademyCustomerAccess(customer_id=kunde_user.id, course_id=kurs.id))
    db.commit()

    # Act
    bericht = kennungen_nachziehen(db)

    # Assert
    zeile = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == kurs.id).first()
    assert zeile.customer_id == kunde_user.id
    assert bericht["umgeschrieben"] == 0


def test_zweimal_laufen_aendert_nichts(db, kurs, kunde_mit_betrieb):
    # Arrange
    nutzer, betrieb = kunde_mit_betrieb
    db.add(AcademyCustomerAccess(customer_id=betrieb, course_id=kurs.id))
    db.commit()

    # Act
    kennungen_nachziehen(db)
    zweiter = kennungen_nachziehen(db)

    # Assert
    assert zweiter["umgeschrieben"] == 0
    assert db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == kurs.id).count() == 1


def test_auch_die_modulzuweisung_wird_nachgezogen(db, kurs, kunde_mit_betrieb):
    # Arrange
    nutzer, betrieb = kunde_mit_betrieb
    modul = AcademyModule(course_id=kurs.id, title="Nachtragprobe Modul")
    db.add(modul)
    db.commit()
    db.refresh(modul)
    db.add(AcademyModuleAccess(customer_id=betrieb, module_id=modul.id))
    db.commit()

    try:
        # Act
        kennungen_nachziehen(db)

        # Assert
        zeile = db.query(AcademyModuleAccess).filter(
            AcademyModuleAccess.module_id == modul.id).first()
        assert zeile.customer_id == nutzer.id
    finally:
        db.query(AcademyModuleAccess).filter(
            AcademyModuleAccess.module_id == modul.id).delete(synchronize_session=False)
        db.delete(modul)
        db.commit()


# ── Verwaiste Zeilen ─────────────────────────────────────────────────────
#
# **Am 2026-08-23 produktiv nachgemessen, und der Befund war ein anderer als
# notiert.** Der Eintrag L-54 sagte, offen bleibe „genau der zweideutige
# Rest". Produktiv gibt es davon **keine einzige** Zeile — dafür tragen
# **beide** vorhandenen Zuweisungen (29.04.2026, Kurs 2 und 8) die Nummer 78:
# Betrieb „Textilpflege Noll", der **kein Kundenkonto** hat.
#
# Der Nachtrag ging daran stumm vorbei. `nach_betrieb.get(78)` ist `None`,
# und `None` fiel in dasselbe `continue` wie „ist schon eine Benutzernummer" —
# der harmlose Fall. Im Startprotokoll stand deshalb nichts, obwohl 2 von 2
# produktiven Zeilen in dieser Klasse liegen.
#
# Sie sind ungefährlich: Ohne Konto sieht sie niemand. Aber sie sind auch
# nicht aufräumbar, solange sie niemand nennt.


@pytest.fixture
def betrieb_ohne_konto(db):
    """Ein Betrieb mit hoher Nummer und ohne Kundenkonto — wie Betrieb 78."""
    hoechste = db.query(User.id).order_by(User.id.desc()).first()
    hoch = (hoechste[0] if hoechste else 0) + 7000

    db.execute(text("INSERT INTO leads (id, company_name) VALUES (:i, :n)"),
               {"i": hoch, "n": "Verwaistprobe Betrieb"})
    db.commit()

    yield hoch

    db.execute(text("DELETE FROM leads WHERE id = :i"), {"i": hoch})
    db.commit()


def test_eine_zeile_ohne_kundenkonto_wird_als_verwaist_gemeldet(
        db, kurs, betrieb_ohne_konto):
    """Der produktive Fall: Zuweisung an einen Betrieb, der keinen Zugang hat."""
    # Arrange
    db.add(AcademyCustomerAccess(customer_id=betrieb_ohne_konto,
                                 course_id=kurs.id))
    db.commit()

    # Act
    bericht = kennungen_nachziehen(db)

    # Assert
    assert bericht["verwaist"] >= 1
    zeile = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == kurs.id).first()
    assert zeile.customer_id == betrieb_ohne_konto, "nicht umschreiben"


def test_eine_kennung_ohne_jede_entsprechung_gilt_auch_als_verwaist(db, kurs):
    """Weder Benutzer- noch Betriebsnummer — erst recht sieht sie niemand."""
    # Arrange
    hoechste = db.query(User.id).order_by(User.id.desc()).first()
    nirgends = (hoechste[0] if hoechste else 0) + 9000
    db.add(AcademyCustomerAccess(customer_id=nirgends, course_id=kurs.id))
    db.commit()

    # Act
    bericht = kennungen_nachziehen(db)

    # Assert
    assert bericht["verwaist"] >= 1


def test_eine_gueltige_benutzernummer_gilt_nicht_als_verwaist(
        db, kurs, kunde_mit_betrieb):
    """Die Abgrenzung: der harmlose Fall darf nicht mitgezählt werden."""
    # Arrange
    nutzer, _ = kunde_mit_betrieb
    db.add(AcademyCustomerAccess(customer_id=nutzer.id, course_id=kurs.id))
    db.commit()

    # Act
    bericht = kennungen_nachziehen(db)

    # Assert
    assert bericht["verwaist"] == 0
