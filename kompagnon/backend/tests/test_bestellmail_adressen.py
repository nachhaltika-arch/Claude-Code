# -*- coding: utf-8 -*-
"""Die Links der Bestellmail zeigen auf die API, nie auf das Frontend (L-156).

**Der Anlass (04.09.2026, erster Systemdurchlauf).** Abruf- und Rechnungslink
entstanden als ``os.getenv("BACKEND_URL", "") or _frontend_adresse()``. Die
Variable steht in keinem der drei Blueprints; ohne sie ging die Mail mit
``<Frontend>/api/shop/download/<token>`` hinaus — an eine Static Site, die
keine API kennt.

**Das ist die Form von L-145**, nur in der Gegenrichtung und in einer Mail,
die schon beim Kunden liegt, wenn es auffaellt.

Die Aufloesung ist keine neue Variable, sondern die vorhandene Kette aus
`services/base_urls.py`: ``API_BASE_URL``, sonst ``RENDER_EXTERNAL_URL``, das
Render je Dienst selbst setzt. Damit stimmt die Adresse in jeder Umgebung,
ohne dass jemand etwas eintragen muss.
"""
from routers.shop import _backend_adresse


def test_ohne_jede_variable_zeigt_der_link_nicht_auf_das_frontend(monkeypatch):
    """Der Fehlerfall aus dem Durchlauf — und der einzige, der beim Kunden
    ankommt."""
    for schluessel in ("BACKEND_URL", "API_BASE_URL", "RENDER_EXTERNAL_URL"):
        monkeypatch.delenv(schluessel, raising=False)
    monkeypatch.setenv("FRONTEND_URL", "https://kas.example")

    adresse = _backend_adresse()

    assert "kas.example" not in adresse
    assert adresse.startswith("https://api.")


def test_auf_render_genuegt_die_eigene_dienstadresse(monkeypatch):
    """Render setzt `RENDER_EXTERNAL_URL` je Dienst selbst — deshalb muss
    `BACKEND_URL` in keinem Blueprint stehen."""
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://backend-staging.onrender.com")
    monkeypatch.setenv("FRONTEND_URL", "https://frontend-staging.onrender.com")

    assert _backend_adresse() == "https://backend-staging.onrender.com"


def test_ein_gesetztes_backend_url_gilt_weiter(monkeypatch):
    """Rueckwaertsvertraeglich: Wo der Wert heute im Dashboard steht, bleibt
    er massgeblich."""
    monkeypatch.setenv("BACKEND_URL", "https://api.beispiel.de/")
    monkeypatch.setenv("API_BASE_URL", "https://anders.example")

    assert _backend_adresse() == "https://api.beispiel.de"
