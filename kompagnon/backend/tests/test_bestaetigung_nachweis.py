"""Wer hat bestätigt — und woran erkennt man eine Maschine?

Offene Frage vom 16.08.2026: Um 16:12:09 kam eine Bestätigung per POST, und
im Protokoll stand keine Abweisung. Wer sie ausgelöst hat, war nicht
feststellbar.

**Nicht, weil der Nachweis fehlte — sondern weil ihn niemand zu sehen bekam.**
`verified_user_agent` und `verified_ip` werden beim Bestätigen festgehalten,
die Übersicht unter „Akquise" zeigt aber nur „bestätigt: ja/nein". Die Antwort
lag in der Datenbank und war aus dem Tool heraus nicht zu erreichen.

Für die Rechenschaftspflicht nach Art. 5 Abs. 2 DSGVO ist das der Kern: Eine
Einwilligung, die man nicht belegen kann, ist im Streitfall keine. Und eine,
die ein Postfach-Scanner erteilt hat, ist auch keine — nur sieht man ihr das
ohne diese Angaben nicht an.

Die Liste ist Admin-Sache und bleibt es: Es sind personenbezogene Daten, die
allein zum Nachweis erhoben werden.
"""
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def bestaetigte_anfrage(app):
    """Eine Anfrage, die bestätigt wurde — mit Spuren."""
    from database import SessionLocal, AuditResult, WidgetRequest

    db = SessionLocal()
    try:
        audit = AuditResult(website_url="https://pytest-nachweis.de",
                            company_name="Pytest Nachweis", status="completed")
        db.add(audit)
        db.commit()
        db.refresh(audit)

        angefragt = datetime.utcnow() - timedelta(minutes=5)
        zeile = WidgetRequest(
            email="besucher@pytest-nachweis.de",
            website_url="https://pytest-nachweis.de",
            audit_id=audit.id,
            poll_token="pytest-nachweis-poll",
            verify_token="pytest-nachweis-verify",
            created_at=angefragt,
            verify_sent_at=angefragt,
            verified_at=angefragt + timedelta(seconds=94),
            verified_user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5) Safari/605.1",
            verified_ip="93.184.216.34",
        )
        db.add(zeile)
        db.commit()
        db.refresh(zeile)
        return zeile.id
    finally:
        db.close()


def _eintrag(client, auth_headers, anfrage_id):
    antwort = client.get("/api/acquisition/widget/requests", headers=auth_headers)
    assert antwort.status_code == 200
    for eintrag in antwort.json()["requests"]:
        if eintrag["id"] == anfrage_id:
            return eintrag
    raise AssertionError("Anfrage fehlt in der Liste")


def test_die_spuren_der_bestaetigung_sind_sichtbar(client, auth_headers,
                                                   bestaetigte_anfrage):
    eintrag = _eintrag(client, auth_headers, bestaetigte_anfrage)

    assert eintrag["verified_user_agent"].startswith("Mozilla/5.0 (iPhone")
    assert eintrag["verified_ip"] == "93.184.216.34"
    assert eintrag["verified_at"] is not None


def test_die_dauer_bis_zur_bestaetigung_wird_genannt(client, auth_headers,
                                                     bestaetigte_anfrage):
    """Ein Mensch braucht Sekunden bis Minuten. Ein Scanner braucht keine.

    Am 16.08. kam die Berichts-Mail fünfzehn Sekunden nach der ersten. Diese
    Zahl ist das schärfste Merkmal, das ohne fremde Hilfe zu haben ist.
    """
    eintrag = _eintrag(client, auth_headers, bestaetigte_anfrage)

    assert eintrag["verify_dauer_s"] == 94


def test_eine_unbestaetigte_anfrage_traegt_keine_spuren(client, auth_headers, app):
    from database import SessionLocal, WidgetRequest

    db = SessionLocal()
    try:
        zeile = WidgetRequest(email="offen@pytest-nachweis.de",
                              website_url="https://pytest-nachweis.de",
                              poll_token="pytest-offen", verify_token="pytest-offen-v")
        db.add(zeile)
        db.commit()
        db.refresh(zeile)
        offen_id = zeile.id
    finally:
        db.close()

    eintrag = _eintrag(client, auth_headers, offen_id)

    assert eintrag["verified"] is False
    assert eintrag["verified_user_agent"] is None
    assert eintrag["verify_dauer_s"] is None


def test_verdaechtig_schnell_wird_benannt(client, auth_headers, app):
    """Unter zwei Sekunden hat niemand gelesen, verstanden und gedrückt."""
    from database import SessionLocal, WidgetRequest

    db = SessionLocal()
    try:
        gesendet = datetime.utcnow() - timedelta(minutes=3)
        zeile = WidgetRequest(
            email="scanner@pytest-nachweis.de",
            website_url="https://pytest-nachweis.de",
            poll_token="pytest-schnell", verify_token="pytest-schnell-v",
            verify_sent_at=gesendet,
            verified_at=gesendet + timedelta(seconds=1),
            verified_user_agent="Mozilla/5.0 (compatible; Barracuda-LinkProtect)",
            verified_ip="10.0.0.1",
        )
        db.add(zeile)
        db.commit()
        db.refresh(zeile)
        schnell_id = zeile.id
    finally:
        db.close()

    eintrag = _eintrag(client, auth_headers, schnell_id)

    assert eintrag["verify_dauer_s"] == 1
    assert eintrag["bestaetigung_verdaechtig"] is True


def test_ein_kunde_bekommt_diese_liste_nicht(client, kunde_headers):
    """Es sind personenbezogene Daten, erhoben allein zum Nachweis."""
    antwort = client.get("/api/acquisition/widget/requests", headers=kunde_headers)

    assert antwort.status_code == 403
