# -*- coding: utf-8 -*-
"""Ein Konto, das es schon gibt, an einen Betrieb haengen.

**Der Anlass (25.08.2026, am selben Tag wie die Zweitzugaenge).** Die
Einladung weist eine bekannte Adresse mit 409 ab — absichtlich: Niemand soll
still den Zugang eines Menschen zu *seinem* Betrieb wegnehmen. Nur blieb
damit kein Weg, es **absichtlich** zu tun. David hat genau danach gefragt:
„wie verbinde ich den Benutzer wenn er schon angelegt ist?"

**Die Regel hiess nie „nie umhaengen", sondern „nicht still umhaengen".**
Deshalb zwei Faelle mit zwei Antworten:

- Konto **ohne** Betrieb: direkt verbinden. Da ist nichts zu verlieren.
- Konto **eines anderen** Betriebs: erst wenn der Aufrufer den alten Betrieb
  genannt bekommen und ausdruecklich bestaetigt hat. Die Antwort auf den
  ersten Versuch nennt ihn beim Namen.

**Ein Mitarbeiterkonto wird nie angehaengt.** Admin, Auditor und Innendienst
gehoeren keinem Betrieb; ein `lead_id` daran waere im besten Fall verwirrend
und im schlechten der Anfang einer Rechtevermischung.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")

BESTAND = "pytest-bestandskonto@kompagnon.local"
BETRIEB_A = "Verbinden Betrieb A GmbH"
BETRIEB_B = "Verbinden Betrieb B GmbH"
NAMEN = (BETRIEB_A, BETRIEB_B)


@pytest.fixture
def betriebe(app):
    """Zwei Betriebe — das Umhaengen braucht ein Von und ein Nach."""
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        angelegt = []
        for name in NAMEN:
            lead = Lead(company_name=name, trade="Heizung", city="Kassel",
                        status="won")
            db.add(lead)
            db.commit()
            db.refresh(lead)
            angelegt.append(lead.id)
        return angelegt
    finally:
        db.close()


def _konto_anlegen(lead_id=None, rolle="kunde"):
    """Ein Konto, das es schon gibt — mit oder ohne Betrieb."""
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        konto = User(email=BESTAND, password_hash="x", first_name="Petra",
                     last_name="Bestand", role=rolle, lead_id=lead_id,
                     is_active=True, is_verified=True)
        db.add(konto)
        db.commit()
        db.refresh(konto)
        return konto.id
    finally:
        db.close()


GESCHWISTER = "pytest-verbinden-geschwister@kompagnon.local"


@pytest.fixture
def kurs_am_betrieb(betriebe):
    """Betrieb A hat schon einen Zugang, und der hat einen Kurs.

    Ohne dieses Geschwisterkonto gaebe es nichts zu erben — `bestand_uebernehmen`
    liest den Bestand aus den **anderen** Konten des Betriebs, nicht aus einer
    Tabelle am Betrieb selbst. Das ist die Bauart, nicht ein Versehen: Die
    Freischaltung haengt seit jeher an einer Benutzernummer.
    """
    from database import SessionLocal, User
    from modelle_akademie import AcademyCourse, AcademyCustomerAccess

    db = SessionLocal()
    try:
        kurs = AcademyCourse(title="Wallbox verkaufen", audience="customer")
        db.add(kurs)
        db.commit()
        db.refresh(kurs)

        geschwister = User(email=GESCHWISTER, password_hash="x", role="kunde",
                           lead_id=betriebe[0], is_active=True)
        db.add(geschwister)
        db.commit()
        db.refresh(geschwister)

        db.add(AcademyCustomerAccess(customer_id=geschwister.id,
                                     course_id=kurs.id))
        db.commit()
        return kurs.id
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _aufraeumen(app):
    """Konten zuerst, dann die Betriebe — sonst zeigt `users.lead_id` ins Leere.

    Die Testbetriebe gehen mit: `ratenbegrenzung` zaehlt **alle** Leads der
    letzten Stunde, liegengebliebene faerben `test_leads_public` im
    Gesamtlauf rot.
    """
    yield
    from database import Lead, SessionLocal, User
    from modelle_akademie import AcademyCustomerAccess, AcademyModuleAccess

    db = SessionLocal()
    try:
        kennungen = [z[0] for z in db.query(User.id).filter(
            User.email.in_((BESTAND, GESCHWISTER))).all()]
        if kennungen:
            for modell in (AcademyModuleAccess, AcademyCustomerAccess):
                db.query(modell).filter(
                    modell.customer_id.in_(kennungen)).delete(
                        synchronize_session=False)
        db.query(User).filter(User.email.in_((BESTAND, GESCHWISTER))).delete(
            synchronize_session=False)
        betriebe = [z[0] for z in db.query(Lead.id).filter(
            Lead.company_name.in_(NAMEN)).all()]
        if betriebe:
            db.query(User).filter(User.lead_id.in_(betriebe)).update(
                {User.lead_id: None}, synchronize_session=False)
            db.query(Lead).filter(Lead.id.in_(betriebe)).delete(
                synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _verbinden(client, headers, lead_id, bestaetigt=False, email=BESTAND):
    return client.post(f"/api/leads/{lead_id}/zugaenge/verbinden",
                       headers=headers,
                       json={"email": email, "umhaengen_bestaetigt": bestaetigt})


def _lead_id_von(email=BESTAND):
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first().lead_id
    finally:
        db.close()


# ── Wer verbinden darf ───────────────────────────────────────────────

class TestFreigabe:
    def test_der_kunde_verbindet_niemanden(self, client, kunde_headers, betriebe):
        _konto_anlegen()

        assert _verbinden(client, kunde_headers, betriebe[0]).status_code == 403

    def test_ohne_anmeldung_gar_nicht(self, client, betriebe):
        _konto_anlegen()

        antwort = client.post(f"/api/leads/{betriebe[0]}/zugaenge/verbinden",
                              json={"email": BESTAND})

        assert antwort.status_code in (401, 403)


# ── Das Konto gehoert noch niemandem ─────────────────────────────────

class TestOhneBetrieb:
    def test_ein_freies_konto_wird_ohne_rueckfrage_verbunden(
            self, client, auth_headers, betriebe):
        """Da ist nichts zu verlieren — also auch nichts zu bestaetigen."""
        # Arrange
        kennung = _konto_anlegen(lead_id=None)

        # Act
        antwort = _verbinden(client, auth_headers, betriebe[0])

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["id"] == kennung
        assert antwort.json()["umgehaengt_von"] is None
        assert _lead_id_von() == betriebe[0]

    def test_es_erbt_was_der_betrieb_schon_darf(self, client, auth_headers,
                                                betriebe, kurs_am_betrieb):
        """Sonst faende der Verbundene eine leere Akademie — dieselbe Falle,
        die `zugang_bestand` fuer die Einladung loest."""
        from modelle_akademie import AcademyCustomerAccess
        from database import SessionLocal

        kennung = _konto_anlegen(lead_id=None)

        _verbinden(client, auth_headers, betriebe[0])

        db = SessionLocal()
        try:
            zeilen = db.query(AcademyCustomerAccess).filter(
                AcademyCustomerAccess.customer_id == kennung).count()
        finally:
            db.close()
        assert zeilen == 1


# ── Das Konto gehoert einem anderen Betrieb ──────────────────────────

class TestUmhaengen:
    def test_ohne_bestaetigung_passiert_nichts(self, client, auth_headers,
                                               betriebe):
        # Arrange — das Konto haengt an Betrieb B
        _konto_anlegen(lead_id=betriebe[1])

        # Act — verbinden mit A, ohne Bestaetigung
        antwort = _verbinden(client, auth_headers, betriebe[0])

        # Assert
        assert antwort.status_code == 409
        assert _lead_id_von() == betriebe[1], "es wurde still umgehaengt"

    def test_die_absage_nennt_den_alten_betrieb_beim_namen(
            self, client, auth_headers, betriebe):
        """Ein Hinweis, der das Hindernis verschweigt, ist eine Sackgasse —
        dieselbe Lehre wie bei L-56."""
        _konto_anlegen(lead_id=betriebe[1])

        text = _verbinden(client, auth_headers, betriebe[0]).text

        assert BETRIEB_B in text

    def test_mit_bestaetigung_wird_umgehaengt(self, client, auth_headers,
                                              betriebe):
        # Arrange
        _konto_anlegen(lead_id=betriebe[1])

        # Act
        antwort = _verbinden(client, auth_headers, betriebe[0], bestaetigt=True)

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["umgehaengt_von"] == betriebe[1]
        assert _lead_id_von() == betriebe[0]

    def test_der_alte_betrieb_verliert_ihn_wirklich(self, client, auth_headers,
                                                   betriebe):
        """Umhaengen ist kein Kopieren — sonst saehe der alte Betrieb weiter
        einen Zugang, den er nicht mehr hat."""
        _konto_anlegen(lead_id=betriebe[1])

        _verbinden(client, auth_headers, betriebe[0], bestaetigt=True)

        liste = client.get(f"/api/leads/{betriebe[1]}/zugaenge",
                           headers=auth_headers).json()["zugaenge"]
        assert [z for z in liste if z["email"] == BESTAND] == []


    def test_die_freischaltungen_des_alten_betriebs_gehen_mit(
            self, client, auth_headers, betriebe):
        """Eine Freischaltung gehoert dem Betrieb, nicht dem Menschen.

        Naehme er sie mit, behielte er einen Kurs, den sein frueherer Betrieb
        bezahlt hat. Fortschritt und Zertifikate bleiben — die gehoeren ihm.
        """
        # Arrange — das Konto haengt an B und hat dort einen Kurs
        from database import SessionLocal
        from modelle_akademie import AcademyCourse, AcademyCustomerAccess

        kennung = _konto_anlegen(lead_id=betriebe[1])
        db = SessionLocal()
        try:
            kurs = AcademyCourse(title="Nur bei B", audience="customer")
            db.add(kurs)
            db.commit()
            db.refresh(kurs)
            db.add(AcademyCustomerAccess(customer_id=kennung, course_id=kurs.id))
            db.commit()
        finally:
            db.close()

        # Act — nach A umhaengen
        _verbinden(client, auth_headers, betriebe[0], bestaetigt=True)

        # Assert
        db = SessionLocal()
        try:
            uebrig = db.query(AcademyCustomerAccess).filter(
                AcademyCustomerAccess.customer_id == kennung).count()
        finally:
            db.close()
        assert uebrig == 0


# ── Was gar nicht geht ───────────────────────────────────────────────

class TestVerweigert:
    def test_ein_mitarbeiterkonto_wird_nicht_angehaengt(self, client,
                                                        auth_headers, betriebe):
        """Admin, Auditor, Innendienst gehoeren keinem Betrieb."""
        _konto_anlegen(lead_id=None, rolle="admin")

        antwort = _verbinden(client, auth_headers, betriebe[0])

        assert antwort.status_code == 409
        assert _lead_id_von() is None

    def test_eine_unbekannte_adresse_ist_404(self, client, auth_headers,
                                             betriebe):
        """Wer hier landet, wollte einladen — die Antwort sagt das auch."""
        antwort = _verbinden(client, auth_headers, betriebe[0],
                             email="gibt-es-nicht@kompagnon.local")

        assert antwort.status_code == 404
        assert "einladen" in antwort.text.lower()

    def test_schon_an_diesem_betrieb_ist_kein_fehler_zum_suchen(
            self, client, auth_headers, betriebe):
        _konto_anlegen(lead_id=betriebe[0])

        antwort = _verbinden(client, auth_headers, betriebe[0])

        assert antwort.status_code == 409
        assert "bereits" in antwort.text.lower()

    def test_ein_unbekannter_betrieb_ist_404(self, client, auth_headers):
        _konto_anlegen()

        assert _verbinden(client, auth_headers, 999999).status_code == 404
