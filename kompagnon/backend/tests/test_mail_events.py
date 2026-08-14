"""Zustellungsstörungen sichtbar machen.

Anlass: Eine Mail wurde vom Empfänger abgewiesen, weil die Versand-IP des
Anbieters auf einer Blockliste stand. Für die Anwendung sah der Versand
erfolgreich aus — Brevo hatte die Mail angenommen, die Ablehnung kam erst
danach. Der Webhook holt diese Meldung nach.

Der Endpunkt ist ohne Login erreichbar, weil Brevo ihn aufruft. Brevo
signiert seine Webhooks nicht; abgesichert wird er deshalb über ein Geheimnis
in der Adresse. Diese Tests decken die Abwehr ab, nicht den Netzverkehr.
"""
import pytest

from database import Lead, MailEvent, SessionLocal

GEHEIMNIS = "pytest-webhook-geheimnis"


@pytest.fixture(autouse=True)
def geheimnis_gesetzt(monkeypatch):
    monkeypatch.setenv("BREVO_WEBHOOK_SECRET", GEHEIMNIS)


@pytest.fixture
def aufraeumen():
    """Entfernt die angelegten Ereignisse und Leads wieder."""
    adressen = []
    yield adressen
    db = SessionLocal()
    try:
        db.query(MailEvent).filter(MailEvent.email.in_(adressen)).delete(
            synchronize_session=False)
        db.query(Lead).filter(Lead.email.in_(adressen)).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _meldung(**felder) -> dict:
    grund = {
        "event": "hard_bounce",
        "email": "empfaenger@example.de",
        "id": 12345,
        "date": "2026-08-14 11:20:31",
        "message-id": "<202608141120.1234@smtp-relay.brevo.com>",
        "subject": "Ihre Website-Analyse",
        "reason": "554 5.7.1 blocked using bl.spamcop.net",
        "sending_ip": "77.32.148.24",
    }
    grund.update(felder)
    return grund


def _zaehle(adresse: str) -> int:
    db = SessionLocal()
    try:
        return db.query(MailEvent).filter(MailEvent.email == adresse).count()
    finally:
        db.close()


# ── Abwehr ────────────────────────────────────────────────────────────

def test_ohne_gueltiges_geheimnis_wird_nichts_angenommen(client):
    r = client.post("/api/mail-events/brevo/falsches-geheimnis", json=_meldung())

    assert r.status_code == 403
    assert _zaehle("empfaenger@example.de") == 0


def test_ohne_hinterlegtes_geheimnis_bleibt_der_endpunkt_zu(client, monkeypatch):
    """Fail closed: eine Umgebung ohne Geheimnis darf nicht offen stehen."""
    monkeypatch.delenv("BREVO_WEBHOOK_SECRET", raising=False)

    r = client.post(f"/api/mail-events/brevo/{GEHEIMNIS}", json=_meldung())

    assert r.status_code == 403


# ── Was abgelegt wird ─────────────────────────────────────────────────

def test_eine_stoerung_wird_abgelegt(client, aufraeumen):
    aufraeumen.append("empfaenger@example.de")

    r = client.post(f"/api/mail-events/brevo/{GEHEIMNIS}", json=_meldung())

    assert r.status_code == 200
    db = SessionLocal()
    try:
        eintrag = db.query(MailEvent).filter(
            MailEvent.email == "empfaenger@example.de").first()
        assert eintrag.event == "hard_bounce"
        assert "spamcop" in eintrag.reason
        assert eintrag.sending_ip == "77.32.148.24"
        assert eintrag.occurred_at is not None
    finally:
        db.close()


@pytest.mark.parametrize("event", [
    "hard_bounce", "soft_bounce", "blocked", "spam", "invalid_email", "error",
])
def test_alle_stoerungsarten_werden_abgelegt(client, aufraeumen, event):
    adresse = f"{event}@example.de"
    aufraeumen.append(adresse)

    client.post(f"/api/mail-events/brevo/{GEHEIMNIS}",
                json=_meldung(event=event, email=adresse))

    assert _zaehle(adresse) == 1


@pytest.mark.parametrize("event", [
    "delivered", "request", "opened", "unique_opened", "click", "deferred",
])
def test_der_normale_verlauf_flutet_die_tabelle_nicht(client, aufraeumen, event):
    """Zustellungen und Öffnungen beantworten keine Frage, die wir stellen."""
    adresse = f"{event}@example.de"
    aufraeumen.append(adresse)

    r = client.post(f"/api/mail-events/brevo/{GEHEIMNIS}",
                    json=_meldung(event=event, email=adresse))

    # 200, damit Brevo den Versuch nicht endlos wiederholt.
    assert r.status_code == 200
    assert _zaehle(adresse) == 0


def test_dieselbe_meldung_zweimal_ergibt_einen_eintrag(client, aufraeumen):
    """Brevo wiederholt Zustellversuche — doppelt gezählt wäre irreführend."""
    aufraeumen.append("empfaenger@example.de")

    client.post(f"/api/mail-events/brevo/{GEHEIMNIS}", json=_meldung())
    client.post(f"/api/mail-events/brevo/{GEHEIMNIS}", json=_meldung())

    assert _zaehle("empfaenger@example.de") == 1


def test_die_meldung_wird_dem_lead_zugeordnet(client, aufraeumen):
    aufraeumen.append("kunde@beispielbetrieb.de")
    db = SessionLocal()
    try:
        lead = Lead(email="kunde@beispielbetrieb.de", company_name="Beispielbetrieb",
                    website_url="https://beispielbetrieb.de", status="new")
        db.add(lead)
        db.commit()
        lead_id = lead.id
    finally:
        db.close()

    client.post(f"/api/mail-events/brevo/{GEHEIMNIS}",
                json=_meldung(email="kunde@beispielbetrieb.de"))

    db = SessionLocal()
    try:
        eintrag = db.query(MailEvent).filter(
            MailEvent.email == "kunde@beispielbetrieb.de").first()
        assert eintrag.lead_id == lead_id
    finally:
        db.close()


def test_ohne_passenden_lead_wird_die_meldung_trotzdem_behalten(client, aufraeumen):
    aufraeumen.append("niemand@example.de")

    client.post(f"/api/mail-events/brevo/{GEHEIMNIS}",
                json=_meldung(email="niemand@example.de"))

    db = SessionLocal()
    try:
        eintrag = db.query(MailEvent).filter(
            MailEvent.email == "niemand@example.de").first()
        assert eintrag is not None
        assert eintrag.lead_id is None
    finally:
        db.close()


def test_eine_meldung_ohne_adresse_wird_verworfen(client):
    r = client.post(f"/api/mail-events/brevo/{GEHEIMNIS}",
                    json=_meldung(email=""))

    assert r.status_code == 200
    assert _zaehle("") == 0


# ── Abruf im Werkzeug ─────────────────────────────────────────────────

def test_die_stoerungen_eines_leads_sind_abrufbar(client, auth_headers, aufraeumen):
    aufraeumen.append("abruf@beispielbetrieb.de")
    db = SessionLocal()
    try:
        lead = Lead(email="abruf@beispielbetrieb.de", company_name="Abruf GmbH",
                    website_url="https://abruf.de", status="new")
        db.add(lead)
        db.commit()
        lead_id = lead.id
    finally:
        db.close()

    client.post(f"/api/mail-events/brevo/{GEHEIMNIS}",
                json=_meldung(email="abruf@beispielbetrieb.de"))

    antwort = client.get(f"/api/mail-events/lead/{lead_id}", headers=auth_headers)

    assert antwort.status_code == 200
    daten = antwort.json()
    assert daten["anzahl"] == 1
    assert daten["ereignisse"][0]["event"] == "hard_bounce"
    assert "spamcop" in daten["ereignisse"][0]["reason"]


def test_der_abruf_braucht_eine_anmeldung(client):
    assert client.get("/api/mail-events/lead/1").status_code in (401, 403)
