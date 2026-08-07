"""Anmeldung und Zugriffsschutz."""
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def test_login_mit_korrekten_daten_liefert_token(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["role"] == "admin"


def test_login_mit_falschem_passwort_wird_abgelehnt(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": "falsch"},
    )

    assert response.status_code == 401


def test_login_mit_unbekannter_adresse_wird_abgelehnt(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "gibt-es-nicht@kompagnon.local", "password": "egal"},
    )

    assert response.status_code == 401


def test_login_verraet_nicht_ob_die_adresse_existiert(client, admin_user):
    """Gleiche Antwort fuer 'Nutzer unbekannt' und 'Passwort falsch'."""
    unbekannt = client.post(
        "/api/auth/login",
        json={"email": "gibt-es-nicht@kompagnon.local", "password": "egal"},
    )
    falsches_passwort = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": "falsch"},
    )

    assert unbekannt.status_code == falsches_passwort.status_code
    assert unbekannt.json()["detail"] == falsches_passwort.json()["detail"]


def test_geschuetzte_route_ohne_token_wird_abgelehnt(client):
    response = client.get("/api/components")

    assert response.status_code in (401, 403)


def test_geschuetzte_route_mit_ungueltigem_token_wird_abgelehnt(client):
    response = client.get(
        "/api/components",
        headers={"Authorization": "Bearer offensichtlich-ungueltig"},
    )

    assert response.status_code in (401, 403)


def test_geschuetzte_route_mit_gueltigem_token_ist_erreichbar(client, auth_headers):
    response = client.get("/api/components", headers=auth_headers)

    assert response.status_code == 200
