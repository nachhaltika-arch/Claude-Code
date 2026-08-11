"""
Einzelmail-Versand über die Brevo-Transaktions-API.

Bis 2026-08-11 liefen alle Einzelmails über SMTP, das in keiner Umgebung
konfiguriert war — Passwort-Zurücksetzen und Audit-Benachrichtigungen wurden
also nie zugestellt. Diese Tests sichern den neuen Weg ab.
"""
import base64

import pytest

from services import brevo_mail


class _Antwort:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or ""

    def json(self):
        if self._payload is None:
            raise ValueError("kein JSON")
        return self._payload


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", "test-schluessel")


def _abfangen(monkeypatch, antwort):
    """Ersetzt den HTTP-Aufruf und gibt die abgeschickte Nutzlast zurück."""
    gesendet = {}

    def _post(url, json=None, headers=None, timeout=None):
        gesendet["url"] = url
        gesendet["payload"] = json
        gesendet["headers"] = headers
        return antwort

    monkeypatch.setattr(brevo_mail.httpx, "post", _post)
    return gesendet


# ── Verfügbarkeit ─────────────────────────────────────────────────────

def test_ohne_schluessel_nicht_verfuegbar(monkeypatch):
    monkeypatch.delenv("BREVO_API_KEY", raising=False)
    assert brevo_mail.is_available() is False

    ok, meldung = brevo_mail.send("wer@example.de", "Test", "<p>hi</p>")
    assert ok is False
    assert "BREVO_API_KEY" in meldung


def test_mit_schluessel_verfuegbar(key):
    assert brevo_mail.is_available() is True


# ── Versand ───────────────────────────────────────────────────────────

def test_erfolgreicher_versand(key, monkeypatch):
    gesendet = _abfangen(monkeypatch, _Antwort(201, {"messageId": "abc"}))

    ok, meldung = brevo_mail.send(
        "empfaenger@example.de", "Betreff", "<p>Inhalt</p>",
        sender_name="KOMPAGNON", sender_email="noreply@kompagnon.group")

    assert ok is True
    assert gesendet["payload"]["to"] == [{"email": "empfaenger@example.de"}]
    assert gesendet["payload"]["sender"]["email"] == "noreply@kompagnon.group"
    assert gesendet["headers"]["api-key"] == "test-schluessel"


def test_absender_hat_eine_vorgabe(key, monkeypatch):
    gesendet = _abfangen(monkeypatch, _Antwort(201, {}))
    brevo_mail.send("wer@example.de", "Betreff", "<p>x</p>")
    assert gesendet["payload"]["sender"]["email"] == brevo_mail.DEFAULT_SENDER_EMAIL


def test_anhang_wird_base64_kodiert(key, monkeypatch):
    gesendet = _abfangen(monkeypatch, _Antwort(201, {}))

    brevo_mail.send("wer@example.de", "Betreff", "<p>x</p>",
                    attachments=[("Bericht.pdf", b"%PDF-1.4 inhalt", "pdf")])

    anhang = gesendet["payload"]["attachment"][0]
    assert anhang["name"] == "Bericht.pdf"
    assert base64.b64decode(anhang["content"]) == b"%PDF-1.4 inhalt"


def test_ohne_anhang_kein_anhangsfeld(key, monkeypatch):
    gesendet = _abfangen(monkeypatch, _Antwort(201, {}))
    brevo_mail.send("wer@example.de", "Betreff", "<p>x</p>")
    assert "attachment" not in gesendet["payload"]


# ── Fehlermeldungen ───────────────────────────────────────────────────

def test_ungueltiger_schluessel_wird_benannt(key, monkeypatch):
    _abfangen(monkeypatch, _Antwort(401, {"message": "Key not found"}))
    ok, meldung = brevo_mail.send("wer@example.de", "Betreff", "<p>x</p>")
    assert ok is False
    assert "ungültig" in meldung


def test_nicht_verifizierter_absender_wird_erklaert(key, monkeypatch):
    """Der häufigste Brevo-Fehler — die Rohmeldung hilft niemandem weiter."""
    _abfangen(monkeypatch, _Antwort(400, {
        "code": "invalid_parameter",
        "message": "sender email is not valid",
    }))
    ok, meldung = brevo_mail.send("wer@example.de", "Betreff", "<p>x</p>")
    assert ok is False
    assert "nicht verifiziert" in meldung


def test_netzwerkfehler_kippt_nicht_durch(key, monkeypatch):
    def _post(*a, **k):
        raise ConnectionError("weg")

    monkeypatch.setattr(brevo_mail.httpx, "post", _post)
    ok, meldung = brevo_mail.send("wer@example.de", "Betreff", "<p>x</p>")
    assert ok is False
    assert "nicht erreichbar" in meldung
