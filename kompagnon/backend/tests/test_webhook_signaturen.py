"""Eine fehlende Konfiguration heißt „keine Freigabe", nicht „keine Prüfung".

Bis zum 2026-08-16 stand in drei Signaturprüfungen dieselbe Konstruktion:

    if SECRET:            # webhooks.py
        ...prüfen...
    if not secret:        # netlify, trackdesk
        return True

Fehlte die Variable, fand keine Prüfung statt. Produktiv war keine der drei
gesetzt — sieben öffentliche Endpunkte nahmen unsignierte Fremdanfragen an,
fünf davon schrieben Leads in die Datenbank. Live nachgemessen: 200 auf jeden
unsignierten Aufruf.

Diese Tests halten die Richtung fest. Sie prüfen den *unkonfigurierten* Fall
zuerst, weil genau der jahrelang niemandem aufgefallen ist.
"""
import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from main import app
from routers import webhooks, webhooks_trackdesk


@pytest.fixture
def client():
    return TestClient(app)


OFFENE_ENDPUNKTE = ("facebook", "linkedin", "google", "postkarte", "telefon")


# ── Ohne Geheimnis: zu ────────────────────────────────────────────────

@pytest.mark.parametrize("pfad", OFFENE_ENDPUNKTE)
def test_ohne_geheimnis_wird_abgewiesen(client, monkeypatch, pfad):
    """Der Fall, der produktiv galt: Variable fehlt."""
    # Arrange
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)

    # Act
    antwort = client.post(f"/api/webhooks/{pfad}", json={"beliebig": "inhalt"})

    # Assert — 403, nicht 200
    assert antwort.status_code == 403, pfad


def test_eine_leere_variable_zaehlt_als_nicht_gesetzt(client, monkeypatch):
    """In Render ist eine leere Variable schnell angelegt und sagt nichts."""
    # Arrange
    monkeypatch.setenv("WEBHOOK_SECRET", "   ")

    # Act / Assert
    assert client.post("/api/webhooks/facebook", json={}).status_code == 403


# ── Mit Geheimnis: nur die richtige Kennung kommt durch ───────────────

def test_falsche_kennung_wird_abgewiesen(client, monkeypatch):
    # Arrange
    monkeypatch.setenv("WEBHOOK_SECRET", "das-echte")

    # Act / Assert
    assert client.post(
        "/api/webhooks/facebook",
        json={},
        headers={"X-Webhook-Secret": "das-falsche"},
    ).status_code == 403


def test_richtige_kennung_kommt_durch(client, monkeypatch):
    """Kein 403 mehr — der Endpunkt arbeitet."""
    # Arrange
    monkeypatch.setenv("WEBHOOK_SECRET", "das-echte")

    # Act — Inhalt ohne verwertbare Felder, damit kein Lead entsteht
    antwort = client.post(
        "/api/webhooks/facebook",
        content=b"kein-json{{{",
        headers={"X-Webhook-Secret": "das-echte",
                 "Content-Type": "application/json"},
    )

    # Assert
    assert antwort.status_code != 403


def test_das_geheimnis_wird_bei_jedem_aufruf_gelesen(client, monkeypatch):
    """Nicht beim Import — sonst hängt es an der Reihenfolge des Starts.

    Dieselbe Falle hat das Projekt zweimal getroffen: einmal bei den
    Modul-Konstanten für die Adressen, einmal hier.
    """
    # Arrange / Act / Assert — die Variable wechselt zur Laufzeit
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    assert client.post("/api/webhooks/telefon", json={}).status_code == 403

    monkeypatch.setenv("WEBHOOK_SECRET", "jetzt-gesetzt")
    assert client.post(
        "/api/webhooks/telefon",
        content=b"kein-json{{{",
        headers={"X-Webhook-Secret": "jetzt-gesetzt",
                 "Content-Type": "application/json"},
    ).status_code != 403


# ── Netlify und Trackdesk: dieselbe Richtung ──────────────────────────

def test_netlify_ohne_geheimnis_weist_ab(monkeypatch):
    # Arrange
    monkeypatch.delenv("NETLIFY_WEBHOOK_SECRET", raising=False)

    # Act / Assert
    assert webhooks._verify_netlify_signature(b"nutzlast", "sha256=egal") is False


def test_netlify_mit_richtiger_signatur(monkeypatch):
    # Arrange
    monkeypatch.setenv("NETLIFY_WEBHOOK_SECRET", "geheim")
    nutzlast = b"nutzlast"
    signatur = "sha256=" + hmac.new(b"geheim", nutzlast, hashlib.sha256).hexdigest()

    # Act / Assert
    assert webhooks._verify_netlify_signature(nutzlast, signatur) is True


def test_trackdesk_ohne_geheimnis_weist_ab(monkeypatch):
    # Arrange
    monkeypatch.delenv("TRACKDESK_WEBHOOK_SECRET", raising=False)

    # Act / Assert
    assert webhooks_trackdesk._verify_signature(b"nutzlast", "egal") is False


def test_trackdesk_mit_richtiger_signatur(monkeypatch):
    # Arrange
    monkeypatch.setenv("TRACKDESK_WEBHOOK_SECRET", "geheim")
    nutzlast = b"nutzlast"
    signatur = hmac.new(b"geheim", nutzlast, hashlib.sha256).hexdigest()

    # Act / Assert
    assert webhooks_trackdesk._verify_signature(nutzlast, signatur) is True
