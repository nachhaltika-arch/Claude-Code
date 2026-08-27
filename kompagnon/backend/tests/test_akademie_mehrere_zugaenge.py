# -*- coding: utf-8 -*-
"""Ein Kurs gehört dem Betrieb — nicht einem der Menschen darin.

**Warum das eine eigene Prüfung braucht (25.08.2026).** Der Innendienst weist
einen Kurs auf dem **Betriebsblatt** zu, also unter der Betriebsnummer.
Gespeichert wird er unter einer **Benutzernummer** — `_kunde_user_id`
übersetzt dazwischen, und zwar mit `.first()`.

Solange ein Betrieb genau ein Konto hatte, war das richtig. Seit heute kann
er zwei haben, und dann bekäme der Kurs **einen** davon: welchen, entscheidet
die Reihenfolge in der Datenbank. Der zweite Mensch meldet sich an und findet
eine leere Akademie — ohne dass irgendwo ein Fehler steht.

Drei Fälle, und der dritte ist der, den man vergisst:

1. Zuweisen erreicht **jeden** Zugang des Betriebs.
2. Entziehen nimmt es **jedem** wieder weg.
3. Wer **danach** eingeladen wird, bekommt den Bestand mit.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")

ERSTER = "pytest-akademie-eins@kompagnon.local"
ZWEITER = "pytest-akademie-zwei@kompagnon.local"
DRITTER = "pytest-akademie-drei@kompagnon.local"
ADRESSEN = (ERSTER, ZWEITER, DRITTER)

#: Auch der Testbetrieb wird abgeraeumt. `ratenbegrenzung` zaehlt **alle**
#: Leads der letzten Stunde gegen `LIMIT_LEADS_PRO_STUNDE`; liegengebliebene
#: Testbetriebe verbrauchen das Kontingent und faerben `test_leads_public`
#: im Gesamtlauf rot — dieselbe Klasse Fehler, die der Kommentar unten
#: fuer die Zuweisungen beschreibt, nur eine Tabelle weiter.
BETRIEB_NAME = "Akademie Sanitär GmbH"


@pytest.fixture
def betrieb(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = Lead(company_name=BETRIEB_NAME, trade="Sanitär",
                    city="Kassel", status="won")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


@pytest.fixture
def modul(app):
    from database import SessionLocal
    from modelle_akademie import AcademyCourse, AcademyModule

    db = SessionLocal()
    try:
        kurs = AcademyCourse(title="Wärmepumpe verkaufen", audience="customer")
        db.add(kurs)
        db.commit()
        db.refresh(kurs)
        m = AcademyModule(course_id=kurs.id, title="Förderung erklären",
                          is_locked=True)
        db.add(m)
        db.commit()
        db.refresh(m)
        return m.id
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _aufraeumen(app):
    """Erst die Zuweisungen, dann die Konten.

    Andersherum bleiben Zeilen liegen, deren `customer_id` ins Leere zeigt —
    und `zuweisung_kennung.kennungen_nachziehen` meldet sie zu Recht als
    verwaist. Genau das ist am 25.08.2026 passiert: Der Test war für sich
    grün und färbte einen zweiten im Gesamtlauf rot.
    """
    yield
    from database import Lead, SessionLocal, User
    from modelle_akademie import AcademyCustomerAccess, AcademyModuleAccess

    db = SessionLocal()
    try:
        kennungen = [z[0] for z in db.query(User.id).filter(
            User.email.in_(ADRESSEN)).all()]
        if kennungen:
            for modell in (AcademyModuleAccess, AcademyCustomerAccess):
                db.query(modell).filter(
                    modell.customer_id.in_(kennungen)).delete(
                        synchronize_session=False)
        db.query(User).filter(User.email.in_(ADRESSEN)).delete(
            synchronize_session=False)
        betriebe = [z[0] for z in db.query(Lead.id).filter(
            Lead.company_name == BETRIEB_NAME).all()]
        if betriebe:
            db.query(User).filter(User.lead_id.in_(betriebe)).update(
                {User.lead_id: None}, synchronize_session=False)
            db.query(Lead).filter(Lead.id.in_(betriebe)).delete(
                synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _einladen(client, headers, betrieb, email):
    antwort = client.post(f"/api/leads/{betrieb}/zugaenge", headers=headers,
                          json={"email": email, "first_name": "Test",
                                "last_name": "Zugang"})
    assert antwort.status_code == 201, antwort.text
    return antwort.json()["id"]


def _freigeschaltet(modul_id, *user_ids):
    """Welche der genannten Konten das Modul tatsächlich haben."""
    from database import SessionLocal
    from modelle_akademie import AcademyModuleAccess

    db = SessionLocal()
    try:
        zeilen = db.query(AcademyModuleAccess.customer_id).filter(
            AcademyModuleAccess.module_id == modul_id,
            AcademyModuleAccess.customer_id.in_(user_ids)).all()
        return {z[0] for z in zeilen}
    finally:
        db.close()


def test_zuweisen_erreicht_jeden_zugang_des_betriebs(
        client, auth_headers, betrieb, modul):
    eins = _einladen(client, auth_headers, betrieb, ERSTER)
    zwei = _einladen(client, auth_headers, betrieb, ZWEITER)

    antwort = client.post(
        f"/api/academy/customer/{betrieb}/modules/{modul}/assign",
        headers=auth_headers)

    assert antwort.status_code == 200, antwort.text
    assert _freigeschaltet(modul, eins, zwei) == {eins, zwei}


def test_entziehen_nimmt_es_jedem_weg(client, auth_headers, betrieb, modul):
    eins = _einladen(client, auth_headers, betrieb, ERSTER)
    zwei = _einladen(client, auth_headers, betrieb, ZWEITER)
    client.post(f"/api/academy/customer/{betrieb}/modules/{modul}/assign",
                headers=auth_headers)

    antwort = client.delete(f"/api/academy/customer/{betrieb}/modules/{modul}",
                            headers=auth_headers)

    assert antwort.status_code == 200, antwort.text
    assert _freigeschaltet(modul, eins, zwei) == set()


def test_wer_spaeter_dazukommt_bekommt_den_bestand_mit(
        client, auth_headers, betrieb, modul):
    """Der Fall, den man vergisst: erst zuweisen, dann einladen."""
    eins = _einladen(client, auth_headers, betrieb, ERSTER)
    client.post(f"/api/academy/customer/{betrieb}/modules/{modul}/assign",
                headers=auth_headers)

    drei = _einladen(client, auth_headers, betrieb, DRITTER)

    assert _freigeschaltet(modul, eins, drei) == {eins, drei}, (
        "der später Eingeladene sieht eine leere Akademie")


def test_ein_zweiter_lauf_meldet_nicht_faelschlich_bereits_zugewiesen(
        client, auth_headers, betrieb, modul):
    """Der neu Eingeladene hat das Modul schon; die Zuweisung darf daran
    nicht scheitern, sonst blockiert ein Nachzügler den ganzen Betrieb."""
    _einladen(client, auth_headers, betrieb, ERSTER)
    client.post(f"/api/academy/customer/{betrieb}/modules/{modul}/assign",
                headers=auth_headers)
    _einladen(client, auth_headers, betrieb, ZWEITER)

    nochmal = client.post(
        f"/api/academy/customer/{betrieb}/modules/{modul}/assign",
        headers=auth_headers)

    assert nochmal.status_code == 409, "alle haben es bereits — das ist 409"
