# -*- coding: utf-8 -*-
"""Antworten von Kunden landen im Werkzeug, nicht nur im Postfach.

**Der Anlass (26.08.2026, Entscheidung David: Brevo Inbound Parsing).**
Die Glocke meldet Tickets und Chatnachrichten (L-18) — E-Mail fehlte, und
zwar nicht aus Versehen: `communications.direction` kennt `inbound`, aber
**keine Zeile im Bestand schreibt es**. Wer auf eine unserer Mails
antwortete, landete in Davids Postfach; das Werkzeug erfuhr nichts.

**Warum die Mail zum Chat wird und nicht in `communications`.**
`communications` hängt an einem **Projekt** und wird von niemandem gelesen.
`Message` dagegen trägt seit jeher `channel` mit den Werten `in_app` und
`email` — die Ablage war vorgesehen, nur nie befüllt. So steht die Antwort
im selben Verlauf wie der Chat: Der Innendienst sieht sie am Betrieb, der
Kunde in seinem Portal, und die Glocke meldet sie wie jede Nachricht.

**Nichts geht still verloren.** Kommt eine Mail von einer Adresse, die zu
keinem Betrieb gehört, wird sie **nicht** weggeworfen — es entsteht eine
Meldung „von unbekannter Adresse". Eine Antwort, die niemand sieht, ist
schlimmer als keine Anbindung: Man verlässt sich darauf.

**Und es wird immer mit 200 geantwortet**, außer das Geheimnis stimmt nicht.
Brevo wiederholt sonst endlos — dieselbe Überlegung wie beim
`mail-events`-Webhook, von dem dieser Weg die Absicherung übernimmt.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")

GEHEIMNIS = "pytest-posteingang-geheim"


ZWEITES = "pytest-posteingang-das-neue"


@pytest.fixture(autouse=True)
def _geheimnis(monkeypatch):
    monkeypatch.setenv("BREVO_INBOUND_SECRET", GEHEIMNIS)
    # Der Regelfall ist **ein** Geheimnis. Das zweite gilt nur waehrend eines
    # Wechsels und wird in den Tests unten eigens gesetzt.
    monkeypatch.delenv("BREVO_INBOUND_SECRET_ALT", raising=False)


class TestWechselOhneFenster:
    """Waehrend des Wechsels gelten beide Geheimnisse (31.08.2026).

    **Warum das noetig ist.** Der Pfad steht an zwei Stellen — in der
    Umgebung bei Render und in der Ziel-URL der Brevo-Route. Beide lassen
    sich nicht im selben Augenblick aendern; wer nur eines gelten laesst, hat
    dazwischen ein Fenster, in dem jede eingehende Mail 403 bekommt.

    **Der Anlass:** Das Geheimnis stand seit dem 28.08. im Klartext im
    Produktivprotokoll, weil es im Pfad liegt und uvicorn jede Anfragezeile
    mit vollem Pfad schreibt. Es muss also gewechselt werden — und ein
    Wechsel, der Kundenantworten kostet, wird nicht gemacht.
    """

    def test_das_alte_gilt_weiter(self, client, monkeypatch):
        monkeypatch.setenv("BREVO_INBOUND_SECRET_ALT", ZWEITES)

        antwort = client.post(f"/api/posteingang/brevo/{GEHEIMNIS}",
                              json={"items": []})

        assert antwort.status_code == 200

    def test_und_das_neue_gilt_schon(self, client, monkeypatch):
        monkeypatch.setenv("BREVO_INBOUND_SECRET_ALT", ZWEITES)

        antwort = client.post(f"/api/posteingang/brevo/{ZWEITES}",
                              json={"items": []})

        assert antwort.status_code == 200

    def test_ein_drittes_gilt_nicht(self, client, monkeypatch):
        """Die Gegenprobe: Zwei erlaubte Werte sind nicht „alles erlaubt"."""
        monkeypatch.setenv("BREVO_INBOUND_SECRET_ALT", ZWEITES)

        antwort = client.post("/api/posteingang/brevo/irgendetwas-anderes",
                              json={"items": []})

        assert antwort.status_code == 403

    def test_nach_dem_wechsel_gilt_das_alte_nicht_mehr(self, client, monkeypatch):
        """Schritt 3 des Ablaufs — und der Grund, warum er nicht vergessen
        werden darf: Bleibt das alte stehen, war der Wechsel keiner."""
        monkeypatch.setenv("BREVO_INBOUND_SECRET", ZWEITES)
        monkeypatch.delenv("BREVO_INBOUND_SECRET_ALT", raising=False)

        assert client.post(f"/api/posteingang/brevo/{ZWEITES}",
                           json={"items": []}).status_code == 200
        assert client.post(f"/api/posteingang/brevo/{GEHEIMNIS}",
                           json={"items": []}).status_code == 403

    def test_ohne_jedes_geheimnis_kommt_niemand_durch(self, client, monkeypatch):
        """Ein leerer Wert darf nicht „alles erlaubt" heissen — das waere der
        gefaehrlichste Ausgang einer misslungenen Umstellung."""
        monkeypatch.delenv("BREVO_INBOUND_SECRET", raising=False)
        monkeypatch.delenv("BREVO_INBOUND_SECRET_ALT", raising=False)

        for weg in ("", "irgendetwas"):
            assert client.post(f"/api/posteingang/brevo/{weg}",
                               json={"items": []}).status_code in (403, 404)


@pytest.fixture
def betrieb(app):
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Posteingang Heizung GmbH",
                    email="chef@posteingang-probe.local", status="won")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        kennung = lead.id
    finally:
        db.close()

    yield kennung

    from database import Benachrichtigung, Message
    db = SessionLocal()
    try:
        db.query(Message).filter(Message.lead_id == kennung).delete(
            synchronize_session=False)
        db.query(Benachrichtigung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _brevo(absender="chef@posteingang-probe.local", betreff="Rückfrage",
           text="Wann geht die Seite online?"):
    """Die Form, die Brevos Inbound Parsing schickt."""
    return {"items": [{
        "From": {"Address": absender, "Name": "Chef"},
        "Subject": betreff,
        "RawTextBody": text,
        "RawHtmlBody": f"<p>{text}</p>",
    }]}


def _zustellen(client, nutzdaten, geheimnis=GEHEIMNIS):
    return client.post(f"/api/posteingang/brevo/{geheimnis}", json=nutzdaten)


class TestEineAntwortKommtAn:
    def test_sie_wird_angenommen(self, client, betrieb):
        assert _zustellen(client, _brevo()).status_code == 200

    def test_sie_steht_im_verlauf_des_betriebs(self, client, betrieb,
                                               auth_headers):
        _zustellen(client, _brevo())

        verlauf = client.get(f"/api/messages/{betrieb}",
                             headers=auth_headers).json()
        inhalte = [m["content"] for m in verlauf]
        assert "Wann geht die Seite online?" in inhalte

    def test_sie_ist_als_mail_gekennzeichnet(self, client, betrieb,
                                             auth_headers):
        """`channel` gibt es seit jeher mit genau diesen zwei Werten — der
        Chat unterscheidet damit, was im Portal getippt und was gemailt
        wurde."""
        _zustellen(client, _brevo())

        eintrag = client.get(f"/api/messages/{betrieb}",
                             headers=auth_headers).json()[-1]
        assert eintrag["channel"] == "email"
        assert eintrag["sender_role"] == "kunde"

    def test_der_betreff_geht_nicht_verloren(self, client, betrieb,
                                             auth_headers):
        _zustellen(client, _brevo(betreff="Termin für den Workshop"))

        eintrag = client.get(f"/api/messages/{betrieb}",
                             headers=auth_headers).json()[-1]
        assert eintrag["subject"] == "Termin für den Workshop"

    def test_die_glocke_meldet_sie(self, client, betrieb):
        _zustellen(client, _brevo())

        from database import Benachrichtigung, SessionLocal
        db = SessionLocal()
        try:
            zeile = db.query(Benachrichtigung).filter(
                Benachrichtigung.art == "mail").first()
        finally:
            db.close()

        assert zeile is not None, "eine Mail loest keine Meldung aus"
        assert zeile.lead_id == betrieb


class TestNichtsGehtStillVerloren:
    def test_eine_unbekannte_adresse_wird_trotzdem_gemeldet(self, client,
                                                            betrieb):
        """Eine Antwort, die niemand sieht, ist schlimmer als keine
        Anbindung — dann verlaesst man sich darauf."""
        _zustellen(client, _brevo(absender="wer-ist-das@fremd.local"))

        from database import Benachrichtigung, SessionLocal
        db = SessionLocal()
        try:
            zeile = db.query(Benachrichtigung).filter(
                Benachrichtigung.art == "mail").first()
        finally:
            db.close()

        assert zeile is not None
        assert zeile.lead_id is None
        assert "wer-ist-das@fremd.local" in (zeile.hinweis or "") + zeile.titel

    def test_und_die_antwort_bleibt_200(self, client, betrieb):
        """Sonst wiederholt Brevo endlos."""
        assert _zustellen(
            client, _brevo(absender="wer-ist-das@fremd.local")).status_code == 200

    def test_auch_ein_kaputter_rumpf_ist_kein_serverfehler(self, client):
        antwort = client.post(f"/api/posteingang/brevo/{GEHEIMNIS}",
                              json={"kein": "posteingang"})

        assert antwort.status_code == 200


class TestDasGeheimnis:
    def test_ein_falsches_oeffnet_nichts(self, client, betrieb):
        assert _zustellen(client, _brevo(), geheimnis="geraten").status_code == 403

    def test_ohne_gesetztes_geheimnis_bleibt_der_weg_zu(self, client, betrieb,
                                                        monkeypatch):
        """Eine halb eingerichtete Umgebung darf nicht offenstehen — dieselbe
        Regel wie beim `mail-events`-Webhook.

        Geprueft wird mit einem *beliebigen* Wert, nicht mit einem leeren:
        Ein leerer Pfadteil ergibt ohnehin 404, und genau den schickt
        niemand, der hereinwill. Die erste Fassung dieses Tests war deshalb
        gruen, ohne die Eigenschaft zu beruehren.
        """
        monkeypatch.setenv("BREVO_INBOUND_SECRET", "")

        assert _zustellen(client, _brevo(),
                          geheimnis="irgendwas").status_code == 403
