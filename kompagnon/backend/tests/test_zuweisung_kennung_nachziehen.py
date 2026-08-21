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
