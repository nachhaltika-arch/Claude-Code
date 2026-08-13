"""Zwei Grenzen für die Kosten — Entscheidung 4.1.

Ein Budget je Projekt (orientiert an den 50 € `ai_tool_costs`, die im
Margenmodell ohnehin kalkuliert sind) und eine Obergrenze pro Nutzer und Tag.
Bei Erreichen erscheint ein freundlicher Hinweis, kein Fehler — der Nutzer hat
nichts falsch gemacht.

Wichtig für den Betrieb: Im Backend gab es bis dahin **kein** Rate-Limiting,
die Zählung ist Teil dieses Features.
"""
from datetime import datetime, timedelta, timezone

import pytest

from services.assistant_budget import (
    GRENZE_NUTZER_PRO_TAG,
    GRENZE_PROJEKT_EURO,
    Verbrauch,
    darf_fragen,
    kosten_fuer,
)


def _jetzt():
    return datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


# ── Kostenrechnung ───────────────────────────────────────────────────────

def test_kosten_wachsen_mit_der_antwortlaenge():
    klein = kosten_fuer(eingabe_tokens=1000, ausgabe_tokens=200)
    gross = kosten_fuer(eingabe_tokens=1000, ausgabe_tokens=2000)

    assert gross > klein > 0


def test_ausgabe_ist_teurer_als_eingabe():
    """Sonst stimmt das Modell der Rechnung nicht mit der Preisliste überein."""
    assert kosten_fuer(0, 1000) > kosten_fuer(1000, 0)


def test_ohne_verbrauch_kostet_es_nichts():
    assert kosten_fuer(0, 0) == 0


# ── Projektbudget ────────────────────────────────────────────────────────

def test_ein_frisches_projekt_darf_fragen():
    entscheidung = darf_fragen(Verbrauch(projekt_euro=0.0, nutzer_anfragen_heute=0))

    assert entscheidung.erlaubt is True
    assert entscheidung.hinweis == ""


def test_ein_ausgeschoepftes_projektbudget_stoppt_freundlich():
    entscheidung = darf_fragen(
        Verbrauch(projekt_euro=GRENZE_PROJEKT_EURO, nutzer_anfragen_heute=0))

    assert entscheidung.erlaubt is False
    # Kein Fehler, kein Vorwurf — und ein Weg nach vorn.
    assert "Team" in entscheidung.hinweis
    assert "Fehler" not in entscheidung.hinweis


def test_knapp_unter_der_grenze_geht_noch():
    entscheidung = darf_fragen(
        Verbrauch(projekt_euro=GRENZE_PROJEKT_EURO - 0.01, nutzer_anfragen_heute=0))

    assert entscheidung.erlaubt is True


def test_vor_der_grenze_wird_gewarnt_ohne_zu_sperren():
    """Ein Hinweis vor der Wand ist mehr wert als die Wand."""
    entscheidung = darf_fragen(
        Verbrauch(projekt_euro=GRENZE_PROJEKT_EURO * 0.85, nutzer_anfragen_heute=0))

    assert entscheidung.erlaubt is True
    assert entscheidung.hinweis != ""


# ── Tageslimit je Nutzer ─────────────────────────────────────────────────

def test_das_tageslimit_greift_unabhaengig_vom_projektbudget():
    entscheidung = darf_fragen(
        Verbrauch(projekt_euro=0.0, nutzer_anfragen_heute=GRENZE_NUTZER_PRO_TAG))

    assert entscheidung.erlaubt is False
    assert "morgen" in entscheidung.hinweis.lower()


def test_eine_anfrage_unter_dem_tageslimit_geht_durch():
    entscheidung = darf_fragen(
        Verbrauch(projekt_euro=0.0, nutzer_anfragen_heute=GRENZE_NUTZER_PRO_TAG - 1))

    assert entscheidung.erlaubt is True


def test_beide_grenzen_gleichzeitig_nennen_die_projektgrenze_zuerst():
    """Sie ist die, die den Nutzer wirklich betrifft — sein Tag endet, das
    Projektbudget nicht."""
    entscheidung = darf_fragen(Verbrauch(projekt_euro=GRENZE_PROJEKT_EURO,
                                         nutzer_anfragen_heute=GRENZE_NUTZER_PRO_TAG))

    assert entscheidung.erlaubt is False
    assert "Team" in entscheidung.hinweis


# ── Der Tag ist der Tag des Nutzers, nicht der des Servers ───────────────

def test_anfragen_von_gestern_zaehlen_nicht_mit():
    from services.assistant_budget import anfragen_heute

    zeiten = [
        _jetzt() - timedelta(days=1, hours=2),   # gestern
        _jetzt() - timedelta(hours=3),           # heute
        _jetzt() - timedelta(minutes=5),         # heute
    ]

    assert anfragen_heute(zeiten, jetzt=_jetzt()) == 2


def test_ohne_zeitstempel_ist_der_tag_leer():
    from services.assistant_budget import anfragen_heute

    assert anfragen_heute([], jetzt=_jetzt()) == 0


@pytest.mark.parametrize("grenze", [GRENZE_PROJEKT_EURO, GRENZE_NUTZER_PRO_TAG])
def test_die_grenzen_sind_konfigurierbar_und_nicht_null(grenze):
    """§ 4.1: Die Grenzwerte gehören in die Konfiguration, nicht in den Code."""
    assert grenze > 0
