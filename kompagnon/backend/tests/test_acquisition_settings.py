"""
Einstellungen unter Akquise: Widget und E-Mail-Zugang.

Der wichtigste Punkt hier ist, dass das SMTP-Passwort verschlüsselt abgelegt
und über die API nie zurückgegeben wird — sonst könnte es jeder Admin-Token
im Klartext auslesen.
"""
import os

import pytest
from cryptography.fernet import Fernet

from database import SessionLocal, SystemSettings
from services import app_settings


@pytest.fixture
def schluessel(monkeypatch):
    monkeypatch.setenv("CREDENTIALS_KEY", Fernet.generate_key().decode())


@pytest.fixture
def db(app):
    """Eigene Session. Hängt an `app`, weil dort das Testschema angelegt wird."""
    session = SessionLocal()
    yield session
    session.query(SystemSettings).filter(
        SystemSettings.key.like("smtp_%")).delete(synchronize_session=False)
    session.query(SystemSettings).filter(
        SystemSettings.key.like("widget_%")).delete(synchronize_session=False)
    session.commit()
    session.close()


# ── Verschlüsselung ───────────────────────────────────────────────────

def test_passwort_wird_verschluesselt_abgelegt(schluessel, db):
    app_settings.set_many(db, {"smtp_password": "streng-geheim"})

    row = db.query(SystemSettings).filter(SystemSettings.key == "smtp_password").first()
    assert row.value.startswith("enc:")
    assert "streng-geheim" not in row.value


def test_passwort_wird_korrekt_zurueckgelesen(schluessel, db):
    app_settings.set_many(db, {"smtp_password": "streng-geheim"})
    assert app_settings.get(db, "smtp_password") == "streng-geheim"


def test_status_enthaelt_niemals_das_passwort(schluessel, db):
    app_settings.set_many(db, {
        "smtp_host": "smtp.example.de", "smtp_user": "post@example.de",
        "smtp_password": "streng-geheim",
    })

    status = app_settings.smtp_status(db)
    assert "streng-geheim" not in str(status)
    assert status["password_set"] is True
    assert status["password_source"] == "datenbank"


def test_leeres_passwort_loescht_das_bestehende_nicht(schluessel, db):
    """Sonst wäre das Passwort weg, sobald jemand das Formular speichert."""
    app_settings.set_many(db, {"smtp_password": "bleibt-erhalten"})
    app_settings.set_many(db, {"smtp_host": "smtp.example.de", "smtp_password": ""})

    assert app_settings.get(db, "smtp_password") == "bleibt-erhalten"


def test_ohne_schluessel_wird_nicht_im_klartext_gespeichert(monkeypatch, db):
    monkeypatch.delenv("CREDENTIALS_KEY", raising=False)
    with pytest.raises(RuntimeError):
        app_settings.set_many(db, {"smtp_password": "darf-nicht-durchkommen"})


# ── Rückfall auf Umgebungsvariablen ───────────────────────────────────

def test_umgebungsvariable_gilt_solange_nichts_gespeichert_ist(monkeypatch, db):
    monkeypatch.setenv("SMTP_HOST", "smtp.aus-der-umgebung.de")
    assert app_settings.get(db, "smtp_host") == "smtp.aus-der-umgebung.de"


def test_gespeicherter_wert_sticht_die_umgebungsvariable(monkeypatch, db):
    monkeypatch.setenv("SMTP_HOST", "smtp.aus-der-umgebung.de")
    app_settings.set_many(db, {"smtp_host": "smtp.aus-der-datenbank.de"})
    assert app_settings.get(db, "smtp_host") == "smtp.aus-der-datenbank.de"


def test_widget_konfiguration_hat_sinnvolle_vorgaben(db):
    config = app_settings.widget_config(db)
    assert set(config) == {"privacy_url", "checkout_url", "headline"}
    assert config["headline"]


# ── Zugriffsschutz ────────────────────────────────────────────────────

@pytest.mark.parametrize("pfad", [
    "/api/acquisition/widget",
    "/api/acquisition/smtp",
])
def test_einstellungen_erfordern_anmeldung(client, pfad):
    assert client.get(pfad).status_code in (401, 403)


def test_test_versand_erfordert_anmeldung(client):
    r = client.post("/api/acquisition/smtp/test", json={"to": "wer@example.de"})
    assert r.status_code in (401, 403)


def test_widget_konfiguration_ist_oeffentlich_aber_ohne_geheimnisse(client):
    """Das Widget läuft auf fremden Seiten und braucht diese Werte ohne Login."""
    r = client.get("/api/widget/config")
    assert r.status_code == 200
    assert set(r.json()) == {"privacy_url", "checkout_url", "headline"}
