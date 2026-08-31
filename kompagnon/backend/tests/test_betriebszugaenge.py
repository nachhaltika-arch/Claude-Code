# -*- coding: utf-8 -*-
"""Mehrere Menschen an einem Betrieb — und wie ein Zugang entsteht.

**Der Anlass (25.08.2026).** Bis heute entstand ein Kundenzugang an genau
einer Stelle: beim Stripe-Kauf, ein Konto je Betrieb. Wer im Betrieb zu
zweit arbeitet — Inhaber und Bueroleitung —, teilte sich ein Passwort. Das
ist kein Randfall, sondern der Normalfall in einem Handwerksbetrieb.

**Zwei Entscheidungen, beide von David am 25.08.2026:**

1. **Der Innendienst laedt ein.** Nicht der Kunde seine Kollegen, nicht
   Selbstregistrierung mit Freigabe. Wer die Daten eines Betriebs sehen
   darf, entscheiden wir — es entsteht kein Weg, auf dem sich jemand selbst
   Zugriff verschafft.
2. **Ein Benutzer gehoert zu einem Betrieb.** `users.lead_id` traegt kein
   UNIQUE, mehrere Konten je Betrieb gehen also ohne Schemaaenderung. Der
   umgekehrte Fall — ein Steuerberater ueber mehreren Betrieben — braeuchte
   eine Zuordnungstabelle und ist bewusst **nicht** gebaut.

Die Einladung erfindet kein zweites Verfahren: Sie setzt denselben
`password_reset_token`, den „Passwort vergessen" benutzt, nur mit einer
laengeren Frist. Ein zweiter Weg zum Passwortsetzen waere ein zweiter Weg,
der falsch sein kann.
"""
import pytest
from datetime import datetime, timedelta

pytestmark = pytest.mark.usefixtures("app")

EINGELADEN = "pytest-zweitzugang@kompagnon.local"

#: Der Betrieb, den jeder Test frisch anlegt. Er wird auch wieder abgeraeumt:
#: `ratenbegrenzung` zaehlt **alle** Leads der letzten Stunde gegen
#: `LIMIT_LEADS_PRO_STUNDE`. Bleiben die Testbetriebe liegen, ist das
#: Kontingent im Gesamtlauf aufgebraucht, und `test_leads_public` bekommt
#: 429 — eine Datei faerbt eine andere rot, ohne sie anzufassen.
BETRIEB_NAME = "Zweitzugang Heizung GmbH"


@pytest.fixture
def betrieb(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = Lead(company_name=BETRIEB_NAME, trade="Heizung",
                    city="Kassel", status="won")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _aufraeumen(app):
    """Die eingeladene Adresse darf keinen Lauf ueberleben — `users.email`
    ist eindeutig, sonst faellt der zweite Testlauf ueber den ersten.

    Der Testbetrieb geht mit: siehe `BETRIEB_NAME`. Erst die Konten, dann
    der Betrieb — andersherum zeigt `users.lead_id` ins Leere.
    """
    yield
    from database import Lead, SessionLocal, User

    db = SessionLocal()
    try:
        betriebe = [z[0] for z in db.query(Lead.id).filter(
            Lead.company_name == BETRIEB_NAME).all()]
        db.query(User).filter(User.email == EINGELADEN).delete(
            synchronize_session=False)
        if betriebe:
            db.query(User).filter(User.lead_id.in_(betriebe)).update(
                {User.lead_id: None}, synchronize_session=False)
            db.query(Lead).filter(Lead.id.in_(betriebe)).delete(
                synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _einladen(client, headers, betrieb, email=EINGELADEN):
    return client.post(f"/api/leads/{betrieb}/zugaenge", headers=headers, json={
        "email": email, "first_name": "Bueroleitung", "last_name": "Muster"})


# ── Wer einladen darf ────────────────────────────────────────────────

class TestFreigabe:
    def test_der_innendienst_legt_einen_zweiten_zugang_an(self, client, auth_headers, betrieb):
        antwort = _einladen(client, auth_headers, betrieb)

        assert antwort.status_code == 201, antwort.text
        assert antwort.json()["email"] == EINGELADEN
        assert antwort.json()["eingeladen"] is True

    def test_der_kunde_laedt_niemanden_ein(self, client, kunde_headers, betrieb):
        """Entscheidung A: Die Freigabe bleibt beim Innendienst."""
        assert _einladen(client, kunde_headers, betrieb).status_code == 403

    def test_ohne_anmeldung_gar_nicht(self, client, betrieb):
        antwort = client.post(f"/api/leads/{betrieb}/zugaenge", json={
            "email": EINGELADEN, "first_name": "A", "last_name": "B"})

        assert antwort.status_code in (401, 403)

    def test_ein_unbekannter_betrieb_ist_404(self, client, auth_headers):
        assert _einladen(client, auth_headers, 999999).status_code == 404


# ── Was die Einladung anrichtet ──────────────────────────────────────

class TestEinladung:
    def test_vor_dem_passwortsetzen_kommt_niemand_hinein(self, client, auth_headers, betrieb):
        """Ein Konto ohne Passwort ist kein offenes Konto."""
        _einladen(client, auth_headers, betrieb)

        antwort = client.post("/api/auth/login", json={
            "email": EINGELADEN, "password": ""})

        assert antwort.status_code == 401

    def test_der_eingeladene_setzt_sein_passwort_und_ist_drin(
            self, client, auth_headers, betrieb):
        _einladen(client, auth_headers, betrieb)

        from database import SessionLocal, User
        db = SessionLocal()
        try:
            neu = db.query(User).filter(User.email == EINGELADEN).first()
            token = neu.password_reset_token
            assert token, "ohne Token kommt der Eingeladene nie an ein Passwort"
        finally:
            db.close()

        gesetzt = client.post("/api/auth/reset-password", json={
            "token": token, "new_password": "zweitzugang-passwort"})
        assert gesetzt.status_code == 200, gesetzt.text

        anmeldung = client.post("/api/auth/login", json={
            "email": EINGELADEN, "password": "zweitzugang-passwort"})
        assert anmeldung.status_code == 200, anmeldung.text

    def test_die_frist_ist_laenger_als_eine_stunde_aber_nicht_endlos(
            self, client, auth_headers, betrieb):
        """Eine Einladung, die ueber Nacht verfaellt, ist keine; eine, die nie
        verfaellt, ist ein liegengebliebener Schluessel."""
        _einladen(client, auth_headers, betrieb)

        from database import SessionLocal, User
        db = SessionLocal()
        try:
            neu = db.query(User).filter(User.email == EINGELADEN).first()
            rest = neu.password_reset_expires - datetime.utcnow()
        finally:
            db.close()

        assert timedelta(days=2) < rest <= timedelta(days=14)

    def test_der_zweite_zugang_sieht_seinen_betrieb(self, client, auth_headers, betrieb):
        _einladen(client, auth_headers, betrieb)

        from database import SessionLocal, User
        db = SessionLocal()
        try:
            neu = db.query(User).filter(User.email == EINGELADEN).first()
            assert neu.lead_id == betrieb
            assert neu.role == "kunde"
        finally:
            db.close()

    def test_eine_vergebene_adresse_wird_nicht_umgehaengt(
            self, client, auth_headers, betrieb, kunde_user):
        """Der gefaehrliche Fall: Eine bestehende Adresse einzuladen duerfte
        **nie** heissen, dass ihr Konto still auf den neuen Betrieb zeigt —
        der Mensch verlöre den Zugang zu seinem eigenen und bekaeme einen
        fremden."""
        vorher = kunde_user.lead_id

        antwort = _einladen(client, auth_headers, betrieb, email=kunde_user.email)

        assert antwort.status_code == 409

        from database import SessionLocal, User
        db = SessionLocal()
        try:
            unveraendert = db.query(User).filter(User.id == kunde_user.id).first()
            assert unveraendert.lead_id == vorher
        finally:
            db.close()


# ── Die Liste und das Entziehen ──────────────────────────────────────

class TestBestand:
    def test_die_liste_nennt_beide_zugaenge(self, client, auth_headers, betrieb):
        _einladen(client, auth_headers, betrieb)

        antwort = client.get(f"/api/leads/{betrieb}/zugaenge", headers=auth_headers)

        assert antwort.status_code == 200
        adressen = [z["email"] for z in antwort.json()["zugaenge"]]
        assert EINGELADEN in adressen

    def test_die_liste_verraet_keinen_token(self, client, auth_headers, betrieb):
        """Wer die Liste sieht, koennte sonst das Passwort eines anderen
        setzen — der Token **ist** der Schluessel."""
        _einladen(client, auth_headers, betrieb)

        roh = client.get(f"/api/leads/{betrieb}/zugaenge", headers=auth_headers).text

        from database import SessionLocal, User
        db = SessionLocal()
        try:
            token = db.query(User).filter(User.email == EINGELADEN).first().password_reset_token
        finally:
            db.close()

        assert token not in roh

    def test_der_kunde_sieht_die_liste_nicht(self, client, kunde_headers, betrieb):
        antwort = client.get(f"/api/leads/{betrieb}/zugaenge", headers=kunde_headers)

        assert antwort.status_code == 403

    def test_ein_entzogener_zugang_kommt_nicht_mehr_hinein(
            self, client, auth_headers, betrieb):
        _einladen(client, auth_headers, betrieb)

        from database import SessionLocal, User
        db = SessionLocal()
        try:
            neu = db.query(User).filter(User.email == EINGELADEN).first()
            neu_id, token = neu.id, neu.password_reset_token
        finally:
            db.close()

        client.post("/api/auth/reset-password", json={
            "token": token, "new_password": "zweitzugang-passwort"})
        assert client.post("/api/auth/login", json={
            "email": EINGELADEN, "password": "zweitzugang-passwort"}).status_code == 200

        entzogen = client.delete(f"/api/leads/{betrieb}/zugaenge/{neu_id}",
                                 headers=auth_headers)
        assert entzogen.status_code == 200, entzogen.text

        gesperrt = client.post("/api/auth/login", json={
            "email": EINGELADEN, "password": "zweitzugang-passwort"})
        assert gesperrt.status_code == 403, "das Konto ist noch offen"

    def test_ein_fremder_zugang_wird_nicht_entzogen(
            self, client, auth_headers, betrieb, kunde_user):
        """Die Zugangs-Kennung allein darf nicht reichen — sie muss zu **dem**
        Betrieb gehoeren, der in der Adresse steht."""
        antwort = client.delete(f"/api/leads/{betrieb}/zugaenge/{kunde_user.id}",
                                headers=auth_headers)

        assert antwort.status_code == 404


# ── Gebaut heisst nicht angeschlossen ────────────────────────────────

import pathlib

FRONTEND = pathlib.Path(__file__).resolve().parents[3] / "kompagnon" / "frontend" / "src"
KOMPONENTE = FRONTEND / "components" / "betrieb" / "Zugaenge.jsx"
#: **Seit dem 31.08.2026 der Reiter, nicht die Seite.** `LeadProfile.jsx`
#: stand mit 2.747 Zeilen ueber der Groessengrenze; die Reiter ziehen einzeln
#: aus (L-25). Der Zugangsbildschirm ist mitgegangen — dieser Test hat den
#: Umzug gemeldet: „die Komponente wird nirgends gerendert", und das stimmte
#: fuer die Datei, in die er sah.
BETRIEBSBLATT = FRONTEND / "components" / "betriebsblatt" / "ReiterZugang.jsx"


def test_die_drei_routen_haben_einen_aufrufer():
    """Fünfmal in diesem Projekt gab es einen Endpunkt, den niemand rief —
    zuletzt acht Tage lang die KI-Nennung. Ein Knopf, den es nicht gibt,
    sieht im Code aus wie eine fertige Funktion."""
    quelle = KOMPONENTE.read_text(encoding="utf-8")

    assert "/zugaenge`, { headers" in quelle or "/zugaenge`, {" in quelle
    assert "method: 'POST'" in quelle, "niemand lädt ein"
    assert "method: 'DELETE'" in quelle, "niemand entzieht"
    assert "/einladung`" in quelle, "die Einladung lässt sich nicht erneuern"


def test_der_bildschirm_haengt_am_betriebsblatt():
    quelle = BETRIEBSBLATT.read_text(encoding="utf-8")

    assert "import Zugaenge" in quelle
    assert "<Zugaenge" in quelle, "die Komponente wird nirgends gerendert"


def test_der_bildschirm_zeigt_keinen_einladungslink():
    """Der Link **ist** der Schlüssel. Wer ihn im Betriebsblatt sieht, kann
    sich als dieser Mensch anmelden — er gehört ausschließlich in die Mail."""
    quelle = KOMPONENTE.read_text(encoding="utf-8")

    assert "reset-password?token" not in quelle
    assert "password_reset_token" not in quelle
