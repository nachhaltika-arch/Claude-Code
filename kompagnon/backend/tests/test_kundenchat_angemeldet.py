# -*- coding: utf-8 -*-
"""Der Kunde schreibt mit dem Innendienst — auch ohne Token in der Adresse.

**Der Auftrag (26.08.2026, David).** Im Kundenportal soll der Chat
eingebaut werden.

**Was schon da war:** `Message` traegt seit jeher beide Richtungen, und der
Innendienst hat den Reiter „Nachrichten" am Betrieb. Auch die Kundenseite
gibt es — `GET`/`POST /api/messages/{lead_id}/kunde`. Sie verlangt aber
einen `customer_token`, denn sie wurde fuer das **Token-Portal** gebaut, das
man ueber den QR-Code ohne Anmeldung betritt.

**Warum das im angemeldeten Portal nicht taugt:** Der Kunde ist dort bereits
angemeldet und traegt seinen Betrieb an seinem Konto. Ihn zusaetzlich einen
Token mitschicken zu lassen hiesse, ihn aus der Oberflaeche zu holen und in
die Adresszeile zu legen — ein Schluessel, der in Verlaufslisten,
Serverprotokollen und geteilten Bildschirmfotos landet.

**Kein zweiter Endpunkt.** Dieselben zwei Routen nehmen jetzt beides: den
Token wie bisher, oder eine Anmeldung. Zwei Wege zum selben Ziel waeren zwei
Wege, die falsch sein koennen — genau der Fehler, den heute Morgen die
Mailanhaenge geliefert haben.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


def _senden(client, headers, lead_id, text="Hallo Innendienst"):
    return client.post(f"/api/messages/{lead_id}/kunde", headers=headers,
                       json={"content": text})


def _lesen(client, headers, lead_id):
    return client.get(f"/api/messages/{lead_id}/kunde", headers=headers)


@pytest.fixture(autouse=True)
def _aufraeumen(app, kunde_user):
    yield
    from database import Message, SessionLocal

    db = SessionLocal()
    try:
        db.query(Message).filter(Message.lead_id == kunde_user.lead_id).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


class TestDerAngemeldeteKunde:
    def test_er_schreibt_ohne_token(self, client, kunde_headers, kunde_user):
        # Act
        antwort = _senden(client, kunde_headers, kunde_user.lead_id)

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["success"] is True

    def test_seine_nachricht_steht_im_verlauf(self, client, kunde_headers,
                                              kunde_user):
        _senden(client, kunde_headers, kunde_user.lead_id, "Wann geht es live?")

        verlauf = _lesen(client, kunde_headers, kunde_user.lead_id).json()

        assert [m["content"] for m in verlauf] == ["Wann geht es live?"]
        assert verlauf[0]["sender_role"] == "kunde"

    def test_er_liest_die_antwort_des_innendienstes(
            self, client, kunde_headers, auth_headers, kunde_user):
        """Der eigentliche Zweck: zwei Richtungen, ein Verlauf."""
        # Arrange — der Innendienst schreibt zuerst
        client.post(f"/api/messages/{kunde_user.lead_id}", headers=auth_headers,
                    json={"content": "Wir starten Montag.", "channel": "in_app"})

        # Act
        verlauf = _lesen(client, kunde_headers, kunde_user.lead_id).json()

        # Assert
        assert "Wir starten Montag." in [m["content"] for m in verlauf]

    def test_ein_leerer_verlauf_ist_kein_fehler(self, client, kunde_headers,
                                                kunde_user):
        antwort = _lesen(client, kunde_headers, kunde_user.lead_id)

        assert antwort.status_code == 200
        assert antwort.json() == []


class TestDieGrenzen:
    def test_ein_fremder_betrieb_bleibt_verschlossen(
            self, client, kunde_headers, fremder_betrieb):
        """Ohne diese Pruefung waere die Anmeldung ein Generalschluessel fuer
        jeden Verlauf — die Kennung steht offen im Pfad."""
        assert _lesen(client, kunde_headers, fremder_betrieb).status_code == 403
        assert _senden(client, kunde_headers, fremder_betrieb).status_code == 403

    def test_ohne_anmeldung_und_ohne_token_gibt_es_nichts(self, client,
                                                          kunde_user):
        antwort = client.get(f"/api/messages/{kunde_user.lead_id}/kunde")

        assert antwort.status_code == 403

    def test_ein_falscher_token_bleibt_falsch(self, client, kunde_user):
        """Der bisherige Weg darf sich nicht gelockert haben."""
        antwort = client.get(f"/api/messages/{kunde_user.lead_id}/kunde",
                             params={"token": "geraten"})

        assert antwort.status_code == 403


class TestDerTokenwegBleibt:
    def test_mit_gueltigem_token_geht_es_weiter_ohne_anmeldung(
            self, client, kunde_user):
        """Das QR-Portal betritt man ohne Konto. Dieser Weg muss bleiben."""
        from database import Lead, SessionLocal

        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == kunde_user.lead_id).first()
            if not lead.customer_token:
                lead.customer_token = "pytest-portal-token"
                db.commit()
            token = lead.customer_token
        finally:
            db.close()

        antwort = client.get(f"/api/messages/{kunde_user.lead_id}/kunde",
                             params={"token": token})

        assert antwort.status_code == 200, antwort.text
