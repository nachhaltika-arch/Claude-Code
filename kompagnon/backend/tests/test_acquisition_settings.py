"""
Einstellungen unter Akquise: Widget und E-Mail-Versand.

Der wichtigste Punkt hier ist, dass hinterlegte Geheimnisse verschlüsselt
abgelegt und über die API nie zurückgegeben werden — sonst könnte sie jeder
Admin-Token im Klartext auslesen.
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


def test_versandweg_meldet_smtp_ohne_das_passwort_zu_zeigen(schluessel, db):
    app_settings.set_many(db, {
        "smtp_host": "smtp.example.de", "smtp_user": "post@example.de",
        "smtp_password": "streng-geheim",
    })

    kanal = app_settings.mail_channel(db)
    assert "streng-geheim" not in str(kanal)
    assert kanal["ready"] is True


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


#: Was das Widget aus der Konfiguration bekommt — abschliessend.
#:
#: **Die Liste steht hier fest, damit ein neuer Wert eine Entscheidung ist.**
#: Das Widget laeuft ohne Login auf fremden Seiten; alles, was hier
#: dazukommt, ist damit oeffentlich. `facebook_pixel_id` kam am 08.09.2026
#: dazu und ist unbedenklich: Eine Pixel-Nummer steht in jeder Seite, die
#: den Pixel laedt, und ist ohne das Werbekonto wertlos.
#: Genau die Schluessel, die das Widget ohne Login bekommt. Die Menge ist
#: **abschliessend**: Wer einen Wert ergaenzt, traegt ihn hier ein und
#: begruendet ihn — sonst waechst eine oeffentliche Route stillschweigend.
#:
#: `check_plus` kam am 10.09.2026 dazu (Entwurf „Teaser Audit + Check PLUS").
#: Es enthaelt Katalogdaten und eine Kaufadresse — Preis, Leistungen,
#: Lieferzeit, Anrechnungsdauer, alles ohnehin oeffentlich. Kein Geheimnis,
#: und der Preis steht damit an **einer** Stelle statt zusaetzlich im Widget.
WIDGET_KONFIGURATION = {"privacy_url", "checkout_url", "headline",
                        "criteria_count", "facebook_pixel_id", "check_plus"}


def test_widget_konfiguration_hat_sinnvolle_vorgaben(db):
    config = app_settings.widget_config(db)
    assert set(config) == WIDGET_KONFIGURATION
    assert config["headline"]
    # Ohne hinterlegte Nummer laedt das Widget kein fremdes Skript.
    assert config["facebook_pixel_id"] == ""
    # **Kein Knopf ohne Ziel.** Frisch aufgesetzt steht Check PLUS auf
    # `draft` und es gibt keine Kaufadresse — dann darf der Block zwar
    # erscheinen, aber nie kaufbar sein.
    angebot = config["check_plus"]
    if angebot is not None:
        assert angebot["verfuegbar"] is False
        assert angebot["url"] == ""


def test_kriterienzahl_stammt_aus_dem_katalog(db):
    """Das Widget nennt diese Zahl dem Interessenten — sie darf nicht raten."""
    from services.audit_criteria import all_criteria

    assert app_settings.widget_config(db)["criteria_count"] == len(all_criteria())


# ── Zugriffsschutz ────────────────────────────────────────────────────

@pytest.mark.parametrize("pfad", [
    "/api/acquisition/widget",
    "/api/acquisition/widget/requests",
    "/api/acquisition/mail",
])
def test_einstellungen_erfordern_anmeldung(client, pfad):
    assert client.get(pfad).status_code in (401, 403)


def test_test_versand_erfordert_anmeldung(client):
    r = client.post("/api/acquisition/mail/test", json={"to": "wer@example.de"})
    assert r.status_code in (401, 403)


def test_versandweg_laesst_sich_nicht_mehr_einstellen(client):
    """Der Zugang kommt aus der Umgebung — ein Schreibweg wäre irreführend."""
    assert client.put("/api/acquisition/smtp", json={"host": "smtp.example.de"}
                      ).status_code in (404, 405)


def test_widget_konfiguration_ist_oeffentlich_aber_ohne_geheimnisse(client):
    """Das Widget läuft auf fremden Seiten und braucht diese Werte ohne Login."""
    r = client.get("/api/widget/config")
    assert r.status_code == 200
    assert set(r.json()) == WIDGET_KONFIGURATION


# ═══════════════════════════════════════════════════════════════════
# Die Kaufadresse fuer Check PLUS (10.09.2026)
# ═══════════════════════════════════════════════════════════════════
#
# **Warum das hier steht.** Der Teaser-Entwurf bringt einen Kaufknopf ins
# Widget, und `check_plus_angebot` schaltet ihn nur frei, wenn eine Adresse
# hinterlegt ist. Die Einstellung selbst war zunaechst **nirgends setzbar** —
# nicht im Formular, nicht in der Schnittstelle. Damit haette es den Knopf
# nie gegeben, und niemand haette gesehen warum: dieselbe Klasse wie
# `RolePermission` vor L-05 und `webhook_actions` vor der Kaufabwicklung —
# ein Bauteil, das sich einstellen laesst und nichts tut, nur andersherum.


def test_die_kaufadresse_laesst_sich_speichern(client, auth_headers):
    r = client.put("/api/acquisition/widget",
                   json={"privacy_url": "", "checkout_url": "", "headline": "H",
                         "facebook_pixel_id": "",
                         "check_plus_url": "https://buy.stripe.com/test123"},
                   headers=auth_headers)
    assert r.status_code == 200, r.text

    gelesen = client.get("/api/acquisition/widget", headers=auth_headers)
    assert gelesen.json()["check_plus_url"] == "https://buy.stripe.com/test123"


def test_eine_unsinnige_adresse_wird_abgewiesen(client, auth_headers):
    # Der Wert landet in einem href auf **fremden** Seiten.
    r = client.put("/api/acquisition/widget",
                   json={"privacy_url": "", "checkout_url": "", "headline": "H",
                         "facebook_pixel_id": "",
                         "check_plus_url": "javascript:alert(1)"},
                   headers=auth_headers)
    assert r.status_code == 400


def test_ohne_angabe_bleibt_es_leer(client, auth_headers):
    r = client.put("/api/acquisition/widget",
                   json={"privacy_url": "", "checkout_url": "", "headline": "H",
                         "facebook_pixel_id": ""},
                   headers=auth_headers)
    assert r.status_code == 200
    assert client.get("/api/acquisition/widget",
                      headers=auth_headers).json()["check_plus_url"] == ""


# ══════════════════════════════════════════════════════════════════════
# Die vier Angebotsaussagen der Berichtsseite (10.09.2026)
# ══════════════════════════════════════════════════════════════════════
#
# Sie wurden von der Berichtsseite gelesen, seit es die Seite gibt — aber
# nirgends geschrieben. Ohne eine Stelle zum Eintragen blieben sie leer, und
# die Kaesten auf der Seite unsichtbar. Das ist das Muster „gebaut, nicht
# angeschlossen": Der Code stimmt, der Knopf fehlt.

def _grundlast(**mehr):
    return {"privacy_url": "", "checkout_url": "", "headline": "H",
            "facebook_pixel_id": "", **mehr}


def test_die_angebotsaussagen_lassen_sich_speichern(client, auth_headers):
    r = client.put("/api/acquisition/widget",
                   json=_grundlast(bericht_rabattsatz="25 % für die ersten 25 Kunden",
                                   bericht_rabattcode="WS25",
                                   bericht_abnahmepunkte="85",
                                   bericht_knappheit="Zwei Sprint-Plätze frei",
                                   bericht_angebotsbegruendung="Eigener Satz."),
                   headers=auth_headers)
    assert r.status_code == 200, r.text

    gelesen = client.get("/api/acquisition/widget", headers=auth_headers).json()
    assert gelesen["bericht_rabattsatz"] == "25 % für die ersten 25 Kunden"
    assert gelesen["bericht_rabattcode"] == "WS25"
    assert gelesen["bericht_abnahmepunkte"] == "85"
    assert gelesen["bericht_knappheit"] == "Zwei Sprint-Plätze frei"
    assert gelesen["bericht_angebotsbegruendung"] == "Eigener Satz."


@pytest.mark.parametrize("unsinn", ["viele", "0", "101", "85 Punkte", "-5"])
def test_eine_abnahmezusage_ohne_punktzahl_wird_abgewiesen(client, auth_headers, unsinn):
    """Sonst steht auf der Kundenseite „mindestens viele Punkte" — und die
    Zusage gilt trotzdem, weil sie dort steht."""
    r = client.put("/api/acquisition/widget",
                   json=_grundlast(bericht_abnahmepunkte=unsinn),
                   headers=auth_headers)
    assert r.status_code == 400


def test_ohne_angabe_wird_nichts_behauptet(client, auth_headers):
    r = client.put("/api/acquisition/widget", json=_grundlast(), headers=auth_headers)
    assert r.status_code == 200
    gelesen = client.get("/api/acquisition/widget", headers=auth_headers).json()
    for feld in ("bericht_rabattsatz", "bericht_rabattcode",
                 "bericht_abnahmepunkte", "bericht_knappheit",
                 "bericht_angebotsbegruendung"):
        assert gelesen[feld] == "", feld
