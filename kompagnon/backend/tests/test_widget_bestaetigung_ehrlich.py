"""Das Widget behauptet keinen Versand, den es nicht gab.

UX-08. Das Widget schrieb nach jeder Analyse „Wir haben eine kurze
Bestätigungs-Mail an … geschickt" — auch dann, wenn der Versand scheiterte.
Der Server weiß es besser: `_notify_widget_requester` protokolliert
„Widget-Bestätigung nicht versendet" und lässt `verify_sent_at` leer. Nur
gesagt hat er es niemandem.

Für den Besucher ist das die schlechteste aller Auskünfte: Er wartet auf eine
Mail, die nie kommt, hält sein Postfach für das Problem und ist weg. Ohne
Bestätigung geht auch der Bericht nie raus — die ganze Strecke endet still.

Die Antwort trägt den Zustand jetzt mit, und es gibt einen zweiten Versuch.
"""
import pytest


@pytest.fixture
def anfrage(app):
    """Eine abgeschlossene Analyse mit Widget-Anfrage, Bestätigung offen.

    Das Token ist je Test eigen: Bei einem festen Token sammeln sich über die
    Tests hinweg Zeilen an, und `.first()` erwischt die falsche.
    """
    import uuid
    from database import SessionLocal, AuditResult, WidgetRequest

    db = SessionLocal()
    try:
        audit = AuditResult(
            website_url="https://beispiel-widget.de",
            company_name="Beispiel Widget GmbH",
            status="completed",
            total_score=61,
            level="silber",
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)

        zeile = WidgetRequest(
            email="besucher@beispiel-widget.de",
            website_url="https://beispiel-widget.de",
            audit_id=audit.id,
            poll_token=f"pytest-poll-{uuid.uuid4()}",
            verify_token=f"pytest-verify-{uuid.uuid4()}",
        )
        db.add(zeile)
        db.commit()
        db.refresh(zeile)
        return {"id": zeile.id, "token": zeile.poll_token}
    finally:
        db.close()


def _setze_versandzeitpunkt(anfrage_id: int):
    from datetime import datetime
    from database import SessionLocal, WidgetRequest

    db = SessionLocal()
    try:
        zeile = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        zeile.verify_sent_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def test_die_kurzfassung_sagt_dass_nichts_raus_ist(client, anfrage):
    antwort = client.get(
        f"/api/widget/teaser/{anfrage['token']}")

    assert antwort.status_code == 200
    assert antwort.json()["bestaetigung_versandt"] is False


def test_die_kurzfassung_sagt_wenn_es_raus_ist(client, anfrage):
    _setze_versandzeitpunkt(anfrage["id"])

    antwort = client.get(
        f"/api/widget/teaser/{anfrage['token']}")

    assert antwort.json()["bestaetigung_versandt"] is True


def test_ein_zweiter_versuch_ist_moeglich(client, anfrage, monkeypatch):
    """Der Besucher soll nicht ratlos dastehen, sondern es erneut anstoßen können."""
    versendet = []
    monkeypatch.setattr(
        "services.email.send_email",
        lambda **kwargs: versendet.append(kwargs) or True,
    )

    antwort = client.post(f"/api/widget/bestaetigung/{anfrage['token']}")

    assert antwort.status_code == 200
    assert antwort.json()["versandt"] is True
    assert len(versendet) == 1


def test_ein_gescheiterter_versuch_wird_als_solcher_gemeldet(client, anfrage, monkeypatch):
    monkeypatch.setattr("services.email.send_email", lambda **kwargs: False)

    antwort = client.post(f"/api/widget/bestaetigung/{anfrage['token']}")

    assert antwort.status_code == 200
    assert antwort.json()["versandt"] is False


def test_was_schon_raus_ist_wird_nicht_erneut_geschickt(client, anfrage, monkeypatch):
    _setze_versandzeitpunkt(anfrage["id"])
    versendet = []
    monkeypatch.setattr(
        "services.email.send_email",
        lambda **kwargs: versendet.append(kwargs) or True,
    )

    antwort = client.post(f"/api/widget/bestaetigung/{anfrage['token']}")

    assert antwort.json()["versandt"] is True
    assert versendet == [], "Ein zweiter Aufruf darf keine zweite Mail auslösen"


def test_der_versuch_ist_begrenzt(client, anfrage, monkeypatch):
    """Sonst ist der Knopf eine Maschine, die eine fremde Adresse zuschüttet.

    Die Empfängeradresse steht fest — wer den Knopf drückt, bestimmt sie
    nicht. Genau deshalb muss die Zahl der Versuche endlich sein.
    """
    monkeypatch.setattr("services.email.send_email", lambda **kwargs: False)

    letzte = None
    for _ in range(6):
        letzte = client.post(f"/api/widget/bestaetigung/{anfrage['token']}")

    assert letzte.status_code == 429


def test_ein_unbekanntes_token_gibt_nichts_preis(client):
    antwort = client.post("/api/widget/bestaetigung/gibtesnicht")

    assert antwort.status_code == 404
