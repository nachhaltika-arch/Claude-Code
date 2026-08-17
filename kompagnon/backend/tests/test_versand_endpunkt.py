"""
Der Not-Aus als Endpunkt: wer ihn sehen darf und wer ihn umlegen darf.

Lesen darf jeder Angemeldete — die Oberflaeche zeigt den Zustand im Menue, und
das muss sie auch dem Auditor zeigen koennen. Umlegen darf nur ein Admin: Ein
Schalter, der allen automatischen Mailversand anhaelt, ist kein Bedienelement
fuer jeden.

Ohne Anmeldung geht gar nichts. Das steht hier ausdruecklich, weil beim Suchen
nach der Ursache des Vorfalls ein Endpunkt auffiel, der genau das nicht
prueft (`PUT /api/projects/{id}`).
"""
import pytest

from services import versandsperre


@pytest.fixture(autouse=True)
def sauberer_ausgangszustand(app):
    """Vor jedem Test kein Eintrag — dann gilt „aus"."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        versandsperre.zuruecksetzen(db)
        yield
        versandsperre.zuruecksetzen(db)
    finally:
        db.close()


# ── Lesen ──────────────────────────────────────────────────────────────

def test_ohne_anmeldung_kein_zugriff(client):
    antwort = client.get("/api/versand/status")

    assert antwort.status_code in (401, 403)


def test_angemeldet_lesbar_und_standard_ist_aus(client, auth_headers):
    antwort = client.get("/api/versand/status", headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json() == {"erlaubt": False}


# ── Umlegen ────────────────────────────────────────────────────────────

def test_ohne_anmeldung_nicht_umlegbar(client):
    antwort = client.put("/api/versand/status", json={"erlaubt": True})

    assert antwort.status_code in (401, 403)


def test_admin_schaltet_ein(client, auth_headers):
    antwort = client.put("/api/versand/status", json={"erlaubt": True}, headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json() == {"erlaubt": True}


def test_die_aenderung_ist_beim_naechsten_lesen_da(client, auth_headers):
    client.put("/api/versand/status", json={"erlaubt": True}, headers=auth_headers)

    assert client.get("/api/versand/status", headers=auth_headers).json() == {"erlaubt": True}


def test_wieder_ausschalten(client, auth_headers):
    client.put("/api/versand/status", json={"erlaubt": True}, headers=auth_headers)
    antwort = client.put("/api/versand/status", json={"erlaubt": False}, headers=auth_headers)

    assert antwort.json() == {"erlaubt": False}


def test_der_schalter_wirkt_auf_die_sperre_selbst(client, auth_headers):
    """Was der Endpunkt sagt, muss auch fuer die Jobs gelten."""
    from database import SessionLocal

    client.put("/api/versand/status", json={"erlaubt": True}, headers=auth_headers)

    db = SessionLocal()
    try:
        assert versandsperre.automatischer_versand_erlaubt(db) is True
    finally:
        db.close()


def test_ein_unsinniger_rumpf_wird_abgewiesen(client, auth_headers):
    antwort = client.put("/api/versand/status", json={"erlaubt": "vielleicht"}, headers=auth_headers)

    assert antwort.status_code == 422
