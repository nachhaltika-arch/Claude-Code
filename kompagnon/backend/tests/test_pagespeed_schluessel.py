"""Wer den PageSpeed-Schlüssel liest — und unter welchem Namen.

In Render heißt die Variable ``PAGESPEED_API_KEY``, im Code hieß sie
``GOOGLE_PAGESPEED_API_KEY``. Am 11.08. wurde das in
``services/audit_pagespeed.py`` repariert, indem dort beide Schreibweisen
gelten. Sieben weitere Stellen lasen weiter allein den langen Namen und sahen
den gesetzten Schlüssel deshalb nicht.

Der Schaden ist leise: PageSpeed v5 antwortet auch ohne Schlüssel, nur mit
einem winzigen Kontingent. Es scheitert also nichts — die Messung fällt nur
unter Last aus, und die Betriebsdiagnose meldete derweil „gesetzt".
"""
import importlib

from services import audit_pagespeed


# ── Die Auflösung selbst ──────────────────────────────────────────────

def test_der_lange_name_gilt(monkeypatch):
    # Arrange
    monkeypatch.setenv("GOOGLE_PAGESPEED_API_KEY", "lang")
    monkeypatch.delenv("PAGESPEED_API_KEY", raising=False)

    # Act / Assert
    assert audit_pagespeed.api_key() == "lang"


def test_der_name_aus_render_gilt_ebenso(monkeypatch):
    """Der Name, unter dem der Schlüssel tatsächlich in Render steht."""
    # Arrange
    monkeypatch.delenv("GOOGLE_PAGESPEED_API_KEY", raising=False)
    monkeypatch.setenv("PAGESPEED_API_KEY", "kurz")

    # Act / Assert
    assert audit_pagespeed.api_key() == "kurz"


def test_ohne_schluessel_bleibt_es_beim_leeren_text(monkeypatch):
    # Arrange
    monkeypatch.delenv("GOOGLE_PAGESPEED_API_KEY", raising=False)
    monkeypatch.delenv("PAGESPEED_API_KEY", raising=False)

    # Act / Assert — kein None, die Aufrufer prüfen auf Wahrheitswert
    assert audit_pagespeed.api_key() == ""


# ── Und alle, die ihn brauchen ────────────────────────────────────────

# Jede Stelle, die vorher ihre eigene os.getenv-Zeile hatte.
LESER = (
    "routers.leads",
    "routers.customers",
    "routers.projects",
    "routers.usercards",
    "automations.scheduler",
    "services.lead_enrichment",
)


def test_jeder_leser_holt_den_schluessel_an_derselben_stelle():
    """Keine zweite Auflösung im Code — sonst driftet sie wieder auseinander."""
    for name in LESER:
        modul = importlib.import_module(name)

        # Assert — dieselbe Funktion, nicht eine eigene Kopie
        assert modul.pagespeed_api_key is audit_pagespeed.api_key, name


def test_der_kurze_name_kommt_ueberall_an(monkeypatch):
    """Der eigentliche Fehler: In Render gesetzt, im Modul unsichtbar."""
    # Arrange — so, wie es produktiv steht
    monkeypatch.delenv("GOOGLE_PAGESPEED_API_KEY", raising=False)
    monkeypatch.setenv("PAGESPEED_API_KEY", "der-echte-schluessel")

    # Act / Assert
    for name in LESER:
        modul = importlib.import_module(name)
        assert modul.pagespeed_api_key() == "der-echte-schluessel", name
