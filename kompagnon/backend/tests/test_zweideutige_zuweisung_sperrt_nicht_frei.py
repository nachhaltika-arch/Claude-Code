"""Eine zweideutige Kennung schaltet niemandem etwas frei (L-54).

**Der Rest, der offen blieb.** Der Nachtrag in `services/zuweisung_kennung.py`
schreibt Altzeilen auf Benutzernummern um — aber **nur wo er sicher ist**.
Ist die Zahl zugleich eine gültige Benutzernummer, bleibt sie liegen: Welche
Bedeutung gemeint war, steht nirgends, und raten wäre schlimmer als nichts
tun, denn ein falsch geratener Eintrag schaltet einem fremden Betrieb etwas
frei.

**Die Notiz dazu sagte: „Heute ungefährlich, weil kein einziger Kurs gesperrt
ist. Gefährlich wird es mit dem ersten gesperrten Kurs."** Genau darauf zu
warten ist die Lücke. Der Lehrplan aus L-60 wird Kurse sperren, und dann
entscheidet eine Zahl aus der Altzeit, wer etwas sieht.

**Deshalb wirkt die Zweideutigkeit jetzt im Lesepfad nicht mehr.** Eine
Zuweisung, deren Kennung sowohl eine Benutzernummer als auch eine
Betriebsnummer mit *anderem* Konto sein kann, zählt nicht als Freischaltung.
Das ist die sichere Richtung: lieber jemandem einen Kurs vorenthalten, den er
haben sollte — das fällt auf und ist in einem Griff behoben — als ihn einem
zu zeigen, der ihn nicht sehen darf.
"""
from datetime import datetime

import pytest


@pytest.fixture
def zweideutige_lage(app):
    """Die Konstellation aus dem Befund, nachgestellt.

    Ein Betrieb, dessen **Nummer** zugleich die Benutzernummer eines
    **anderen** Kontos ist. Genau das ist am 19.08.2026 im Testbestand
    nachgewiesen worden: fremde Betriebs-ID 2 = Benutzer-ID 2.
    """
    from auth import hash_password
    from database import (AcademyCourse, AcademyCustomerAccess, Lead,
                          SessionLocal, User)

    from sqlalchemy import text

    db = SessionLocal()
    try:
        # Das Fixture laeuft je Test einmal und legt feste Adressen an —
        # ohne dieses Aufraeumen scheitert der zweite Test an der Zeile des
        # ersten.
        db.execute(text("DELETE FROM users WHERE email LIKE '%-l54@example.com'"))
        db.execute(text("DELETE FROM academy_courses WHERE title IN "
                        "('Gesperrter Kurs', 'Sauber zugewiesen')"))
        db.commit()

        kurs = AcademyCourse(title="Gesperrter Kurs", is_locked=True,
                             is_published=True)
        db.add(kurs)

        # Der Fremde: Sein Konto bekommt irgendeine Nummer.
        fremder = User(email="fremder-l54@example.com",
                       password_hash=hash_password("egal"), role="kunde",
                       is_active=True)
        db.add(fremder)
        db.commit()
        db.refresh(kurs)
        db.refresh(fremder)

        # Ein Betrieb, dessen id zufaellig der Benutzernummer des Fremden
        # gleicht. Genau diese Ueberschneidung ist der Befund.
        betrieb = Lead(id=fremder.id, company_name=f"Betrieb {fremder.id}",
                       trade="Heizung", city="Kassel")
        db.merge(betrieb)
        db.commit()

        # Dem Betrieb gehoert ein anderes Konto.
        eigner = User(email="eigner-l54@example.com",
                      password_hash=hash_password("egal"), role="kunde",
                      lead_id=fremder.id, is_active=True)
        db.add(eigner)
        db.commit()

        # Die Altzeile: als Kennung steht die **Betriebs**nummer darin —
        # und sie stammt aus der Zeit **vor** dem 19.08.2026, als der
        # Schreibpfad noch nicht aufloeste. Genau das macht sie verdaechtig;
        # eine Zeile von heute waere es nicht.
        db.add(AcademyCustomerAccess(course_id=kurs.id, customer_id=fremder.id,
                                     assigned_at=datetime(2026, 7, 1)))
        db.commit()

        return {"kurs_id": kurs.id, "fremder": fremder.email,
                "kennung": fremder.id}
    finally:
        db.close()


def _anmelden(client, email: str) -> dict:
    antwort = client.post("/api/auth/login",
                          json={"email": email, "password": "egal"})
    assert antwort.status_code == 200, antwort.text[:200]
    return {"Authorization": f"Bearer {antwort.json()['access_token']}"}


def test_der_fremde_sieht_den_gesperrten_kurs_nicht(client, zweideutige_lage):
    """Ohne die Prüfung stünde er in seiner Liste — die Zahl passt ja."""
    headers = _anmelden(client, zweideutige_lage["fremder"])

    kurse = client.get("/api/academy/courses", headers=headers).json()
    ids = {k.get("id") for k in kurse}

    assert zweideutige_lage["kurs_id"] not in ids, (
        "Eine zweideutige Altzeile hat einem fremden Konto einen gesperrten "
        "Kurs freigeschaltet")


def test_auch_die_einzelabfrage_gibt_ihn_nicht_heraus(client, zweideutige_lage):
    """Die Liste zu filtern und das Detail offenzulassen wäre keine Sperre."""
    headers = _anmelden(client, zweideutige_lage["fremder"])

    antwort = client.get(f"/api/academy/courses/{zweideutige_lage['kurs_id']}",
                         headers=headers)

    assert antwort.status_code == 404, antwort.text[:160]


def test_die_zweideutigen_kennungen_sind_benennbar(app, zweideutige_lage):
    """Wer sie im Lesepfad übergeht, muss sie auch nennen können — sonst
    verschwindet der offene Rest aus dem Blick, statt entschieden zu werden."""
    from database import SessionLocal
    from services.zuweisung_kennung import zweideutige_kennungen

    db = SessionLocal()
    try:
        assert zweideutige_lage["kennung"] in zweideutige_kennungen(db)
    finally:
        db.close()


def test_eine_eindeutige_zuweisung_wirkt_weiterhin(client, app):
    """Die Absicherung darf keine gültige Freischaltung wegnehmen."""
    from auth import hash_password
    from database import (AcademyCourse, AcademyCustomerAccess, SessionLocal,
                          User)

    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM users WHERE email = 'sauber-l54@example.com'"))
        db.commit()

        kurs = AcademyCourse(title="Sauber zugewiesen", is_locked=True,
                             is_published=True)
        nutzer = User(email="sauber-l54@example.com",
                      password_hash=hash_password("egal"), role="kunde",
                      is_active=True)
        db.add_all([kurs, nutzer])
        db.commit()
        db.refresh(kurs)
        db.refresh(nutzer)
        db.add(AcademyCustomerAccess(course_id=kurs.id, customer_id=nutzer.id))
        db.commit()
        kurs_id, adresse = kurs.id, nutzer.email
    finally:
        db.close()

    headers = _anmelden(client, adresse)
    ids = {k.get("id") for k in client.get("/api/academy/courses",
                                           headers=headers).json()}

    assert kurs_id in ids, "eine eindeutige Zuweisung wurde mitgesperrt"
