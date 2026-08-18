"""Ob die Dateiablage einen Deploy ueberlebt, muss man von aussen sehen koennen.

Seit dem 17.08. tragen die Blueprints `disk: uploads` (1 GB, `/var/data`) und
`UPLOAD_ROOT`. Ob der Datentraeger produktiv **tatsaechlich eingehaengt** ist,
liess sich bisher nur im Render-Dashboard nachsehen — und wer nicht nachsieht,
merkt es erst, wenn nach dem naechsten Deploy Kundendateien fehlen.

Der Unterschied ist messbar: Ein eingehaengter Datentraeger ist ein eigenes
Dateisystem, hat also eine andere Geraetenummer als `/`. Genau das prueft
`ablage_zustand()` — kein Ratespiel, kein Dashboard.
"""
import os
from pathlib import Path

from services.dateiablage import ablage_zustand, upload_wurzel


def test_ohne_variable_bleibt_es_beim_bisherigen_verzeichnis(monkeypatch):
    monkeypatch.delenv("UPLOAD_ROOT", raising=False)

    assert upload_wurzel() == Path("uploads")


def test_der_zustand_nennt_pfad_und_beschreibbarkeit(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))

    zustand = ablage_zustand()

    assert zustand["pfad"] == str(tmp_path)
    assert zustand["beschreibbar"] is True


def test_ein_verzeichnis_auf_derselben_platte_gilt_nicht_als_dauerhaft(tmp_path, monkeypatch):
    # tmp_path liegt im selben Dateisystem wie die Wurzel — also kein
    # eingehaengter Datentraeger. Genau dieser Fall ist produktiv der
    # gefaehrliche: Es sieht aus, als laege alles richtig.
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))

    assert ablage_zustand()["dauerhaft"] is False


def test_ein_nicht_beschreibbarer_pfad_faellt_auf(tmp_path, monkeypatch):
    gesperrt = tmp_path / "gesperrt"
    gesperrt.mkdir()
    os.chmod(gesperrt, 0o500)
    monkeypatch.setenv("UPLOAD_ROOT", str(gesperrt / "darunter"))

    try:
        zustand = ablage_zustand()
        assert zustand["beschreibbar"] is False
        assert zustand["grund"]
    finally:
        os.chmod(gesperrt, 0o700)


def test_der_zustand_verraet_keine_geheimnisse(tmp_path, monkeypatch):
    """Auf `/info` lagen einmal Datenbank-Zugangsdaten offen. Hier nur Pfad
    und zwei Wahrheitswerte — mehr braucht die Auskunft nicht."""
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))

    assert set(ablage_zustand()) <= {"pfad", "beschreibbar", "dauerhaft", "grund"}


def test_die_gesundheitspruefung_nennt_den_zustand(client):
    """Von aussen abfragbar — sonst muss man ins Dashboard sehen."""
    antwort = client.get("/health").json()

    assert "uploads" in antwort
    assert "dauerhaft" in antwort["uploads"]
