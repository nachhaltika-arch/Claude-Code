# -*- coding: utf-8 -*-
"""Was vom Kunden hereinkommt, soll der Innendienst sehen (L-18).

**Der Auftrag (26.08.2026, David):** „ich brauche eine notification für
tickets, chat oder email die wir vom kunden erhalten."

**Was heute passiert, wenn ein Kunde sich meldet:**

| Weg | Was geschieht |
|---|---|
| Ticket | **Nichts.** `create_ticket` schreibt eine Zeile und schweigt. |
| Chat | Eine Mail an `SMTP_USER` — eine feste Adresse aus der Umgebung. |
| E-Mail | Kommt gar nicht im Werkzeug an (siehe unten). |

L-18 heißt seit Mai „In-App-Benachrichtigungen fehlen (nur E-Mail-Schalter
vorhanden)". Die Schalter unter Einstellungen → Benachrichtigungen sind
obendrein reiner Anzeigezustand: `useState` ohne Speicherung.

**Warum eine eigene Tabelle und nicht „die ungelesenen zusammenzählen".**
Ein Ticket, eine Chatnachricht und eine Mail liegen in drei Tabellen mit drei
Formen. Sie beim Anzeigen zusammenzurechnen hieße, an jeder Stelle alle drei
zu kennen — und die vierte, die dazukommt, wird vergessen. Eine Meldung ist
ein eigener Vorgang: Sie entsteht einmal, sie wird einmal gelesen, und sie
hat ein Ziel, das man anklicken kann.

**E-Mail ist vorbereitet, aber nicht angeschlossen — und das steht hier,
damit es niemand für ein Versehen hält.** `communications.direction` kennt
`inbound`, aber **keine Zeile im Bestand schreibt es**: Antworten von Kunden
landen im echten Postfach, nicht im Werkzeug. Dafür braucht es einen
Posteingang (Brevo Inbound Parsing oder IMAP), und der ist eine
Einrichtungsfrage bei David. Die Meldestelle nimmt `mail` schon entgegen;
angeschlossen wird sie, sobald es etwas anzuschließen gibt.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture(autouse=True)
def _leer(app):
    """Jeder Fall beginnt ohne Meldungen — sonst zaehlt er die des vorigen."""
    from database import Benachrichtigung, SessionLocal

    def weg():
        db = SessionLocal()
        try:
            db.query(Benachrichtigung).delete()
            db.commit()
        finally:
            db.close()

    weg()
    yield
    weg()


def _melden(**felder):
    from database import SessionLocal
    from services.benachrichtigungen import melden

    db = SessionLocal()
    try:
        vorgaben = {"art": "chat", "titel": "Neue Nachricht",
                    "hinweis": "Probe", "ziel": "/app/betriebe/1"}
        return melden(db, **{**vorgaben, **felder})
    finally:
        db.close()


class TestEineMeldungEntsteht:
    def test_der_innendienst_sieht_sie(self, client, auth_headers):
        # Arrange
        _melden(titel="Neue Nachricht von Mustermann")

        # Act
        antwort = client.get("/api/benachrichtigungen", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert [m["titel"] for m in antwort.json()] == ["Neue Nachricht von Mustermann"]

    def test_sie_traegt_ein_ziel_das_man_anklicken_kann(self, client, auth_headers):
        """Eine Meldung ohne Weg dorthin verlangt vom Leser, selbst zu
        suchen — dieselbe Lehre wie bei den Warnungen auf dem Dashboard."""
        _melden(ziel="/app/betriebe/7")

        assert client.get("/api/benachrichtigungen",
                          headers=auth_headers).json()[0]["ziel"] == "/app/betriebe/7"

    def test_die_neueste_steht_oben(self, client, auth_headers):
        _melden(titel="zuerst")
        _melden(titel="danach")

        titel = [m["titel"] for m in client.get("/api/benachrichtigungen",
                                                headers=auth_headers).json()]

        assert titel == ["danach", "zuerst"]

    def test_die_zahl_der_ungelesenen_steht_getrennt_bereit(self, client,
                                                            auth_headers):
        """Fuer die Glocke im Kopf — sie braucht eine Zahl, keine Liste."""
        _melden()
        _melden()

        antwort = client.get("/api/benachrichtigungen/anzahl", headers=auth_headers)

        assert antwort.json()["ungelesen"] == 2


class TestGelesen:
    def test_eine_einzelne_wird_als_gelesen_vermerkt(self, client, auth_headers):
        kennung = _melden()

        client.post(f"/api/benachrichtigungen/{kennung}/gelesen", headers=auth_headers)

        assert client.get("/api/benachrichtigungen/anzahl",
                          headers=auth_headers).json()["ungelesen"] == 0

    def test_gelesene_verschwinden_nicht_sofort(self, client, auth_headers):
        """Wer versehentlich klickt, soll die Meldung noch finden. Geloescht
        wird nichts; die Liste zeigt sie weiter, nur nicht mehr fett."""
        kennung = _melden()

        client.post(f"/api/benachrichtigungen/{kennung}/gelesen", headers=auth_headers)

        eintrag = client.get("/api/benachrichtigungen", headers=auth_headers).json()[0]
        assert eintrag["gelesen"] is True

    def test_alle_auf_einmal(self, client, auth_headers):
        _melden()
        _melden()

        client.post("/api/benachrichtigungen/alle-gelesen", headers=auth_headers)

        assert client.get("/api/benachrichtigungen/anzahl",
                          headers=auth_headers).json()["ungelesen"] == 0

    def test_nur_ungelesene_auf_wunsch(self, client, auth_headers):
        gelesen = _melden(titel="alt")
        _melden(titel="neu")
        client.post(f"/api/benachrichtigungen/{gelesen}/gelesen", headers=auth_headers)

        offen = client.get("/api/benachrichtigungen?nur_ungelesen=true",
                           headers=auth_headers).json()

        assert [m["titel"] for m in offen] == ["neu"]


class TestWerSieSieht:
    def test_ein_kunde_sieht_sie_nicht(self, client, kunde_headers):
        """Sie tragen Betriebsnamen und Betreffzeilen anderer Kunden."""
        _melden()

        assert client.get("/api/benachrichtigungen",
                          headers=kunde_headers).status_code == 403

    def test_ohne_anmeldung_erst_recht_nicht(self, client):
        _melden()

        assert client.get("/api/benachrichtigungen").status_code in (401, 403)

    def test_auch_die_zahl_nicht(self, client, kunde_headers):
        assert client.get("/api/benachrichtigungen/anzahl",
                          headers=kunde_headers).status_code == 403


class TestWasEineMeldungAusloest:
    def test_ein_ticket_meldet_sich(self, client):
        """Bis heute schrieb `create_ticket` eine Zeile und schwieg."""
        antwort = client.post("/api/tickets/", json={
            "user_email": "kunde@probe.local", "user_name": "Anna Probe",
            "type": "bug", "priority": "high",
            "title": "Formular speichert nicht",
            "description": "Beim Klick auf Speichern passiert nichts."})
        assert antwort.status_code == 200, antwort.text

        from database import Benachrichtigung, SessionLocal
        db = SessionLocal()
        try:
            zeile = db.query(Benachrichtigung).order_by(
                Benachrichtigung.id.desc()).first()
        finally:
            db.close()

        assert zeile is not None, "ein Ticket loest keine Meldung aus"
        assert zeile.art == "ticket"
        assert "Formular speichert nicht" in zeile.titel

    def test_eine_chatnachricht_meldet_sich(self, client, kunde_headers,
                                            kunde_user):
        client.post(f"/api/messages/{kunde_user.lead_id}/kunde",
                    headers=kunde_headers, json={"content": "Wann geht es los?"})

        from database import Benachrichtigung, SessionLocal
        db = SessionLocal()
        try:
            zeile = db.query(Benachrichtigung).filter(
                Benachrichtigung.art == "chat").order_by(
                    Benachrichtigung.id.desc()).first()
        finally:
            db.close()

        assert zeile is not None, "eine Kundennachricht loest keine Meldung aus"
        assert zeile.lead_id == kunde_user.lead_id
        assert zeile.ziel.endswith(str(kunde_user.lead_id))

    def test_der_innendienst_loest_keine_meldung_aus(self, client, auth_headers,
                                                     kunde_user):
        """Sonst meldete sich das Werkzeug bei sich selbst — und die Glocke
        waere nach einer Woche Rauschen."""
        client.post(f"/api/messages/{kunde_user.lead_id}", headers=auth_headers,
                    json={"content": "Wir starten Montag.", "channel": "in_app"})

        from database import Benachrichtigung, SessionLocal
        db = SessionLocal()
        try:
            anzahl = db.query(Benachrichtigung).count()
        finally:
            db.close()

        assert anzahl == 0


class TestDerVersandDarfNichtsKaputtmachen:
    def test_eine_kaputte_meldestelle_verhindert_die_nachricht_nicht(
            self, client, kunde_headers, kunde_user, monkeypatch):
        """Die Meldung ist Beiwerk, die Nachricht des Kunden ist die
        Hauptsache. Genau andersherum ging heute Morgen die Willkommensmail
        verloren — ein Fehler im Beiwerk riss den ganzen Vorgang mit.
        """
        import services.benachrichtigungen as modul

        def kaputt(*a, **k):
            raise RuntimeError("Meldestelle streikt")

        monkeypatch.setattr(modul, "melden", kaputt)

        antwort = client.post(f"/api/messages/{kunde_user.lead_id}/kunde",
                              headers=kunde_headers, json={"content": "trotzdem"})

        assert antwort.status_code == 200, antwort.text
