"""Betriebsbereitschaft — der Endpunkt, den Render fuer den Health-Check nutzt."""


def test_health_meldet_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_health_braucht_keine_anmeldung(client):
    """Sonst wuerde Render den Dienst als tot einstufen."""
    response = client.get("/health")

    assert response.status_code == 200
