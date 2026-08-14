"""Freitext-Branche → Branchenklasse.

Bewertungslogik 2026.2, § 2.3: Das Modell erkennt und meldet Freitext, die
Klasse bestimmt der Code. Der Grund steht im Dokument: Eine nicht
deterministische Zuordnung hiesse, dass dieselbe Website an zwei Tagen gegen
zwei Maßstäbe läuft — damit wäre die Wiederholbarkeit eines Standards dahin.
"""
import pytest

from services.audit_industry_map import (
    KLASSEN,
    klasse_fuer_branche,
    nicht_zugeordnet,
)


# ── Die sechs Klassen ─────────────────────────────────────────────────

def test_alle_sechs_klassen_sind_beschrieben():
    assert set(KLASSEN) == {"K1", "K2", "K3", "K4", "K5", "K6"}
    for schluessel, klasse in KLASSEN.items():
        assert klasse.bezeichnung, schluessel
        assert klasse.merkmal, schluessel


# ── Zuordnung nach Stichwort ──────────────────────────────────────────

@pytest.mark.parametrize("branche,erwartet", [
    ("Heizung und Sanitär", "K1"),
    ("Dachdecker", "K1"),
    ("Dachdeckerei mit Zimmerei und Bauklempnerei", "K1"),
    ("Elektrotechnik", "K1"),
    ("Kfz-Werkstatt", "K1"),
    ("Garten- und Landschaftsbau", "K1"),
    ("Steuerberatung mit Schwerpunkt Handwerk", "K2"),
    ("Zahnarztpraxis", "K2"),
    ("Rechtsanwaltskanzlei", "K2"),
    ("Physiotherapie", "K2"),
    ("Architekturbüro", "K2"),
    ("Restaurant", "K3"),
    ("Friseursalon", "K3"),
    ("Hotel garni", "K3"),
    ("Werbeagentur", "K4"),
    ("Unternehmensberatung", "K4"),
    ("Softwareentwicklung", "K4"),
    ("Onlineshop für Ersatzteile", "K5"),
    ("politischer Kandidat (Stadtratswahl)", "K6"),
    ("Verein", "K6"),
    ("Blog über Reisen", "K6"),
])
def test_die_branche_wird_ihrer_klasse_zugeordnet(branche, erwartet):
    zuordnung = klasse_fuer_branche(branche, betriebsseite=True)
    assert zuordnung.klasse == erwartet, branche
    assert zuordnung.quelle == "map"


def test_gross_und_kleinschreibung_spielt_keine_rolle():
    assert klasse_fuer_branche("DACHDECKER", betriebsseite=True).klasse == "K1"
    assert klasse_fuer_branche("steuerberatung", betriebsseite=True).klasse == "K2"


def test_die_spezifischere_regel_gewinnt():
    """„Steuerberatung für Handwerksbetriebe" ist eine Kanzlei, kein Handwerk."""
    assert klasse_fuer_branche(
        "Steuerberatung für Handwerksbetriebe", betriebsseite=True).klasse == "K2"


# ── Rückfall, wenn keine Regel greift (§ 2.3 Punkt 3) ─────────────────

def test_ohne_treffer_gilt_k1_wenn_ein_betrieb_dahintersteht():
    zuordnung = klasse_fuer_branche("Zauberschule", betriebsseite=True)

    assert zuordnung.klasse == "K1"
    assert zuordnung.quelle == "rueckfall"


def test_ohne_treffer_gilt_k6_wenn_kein_betrieb_dahintersteht():
    zuordnung = klasse_fuer_branche("Zauberschule", betriebsseite=False)

    assert zuordnung.klasse == "K6"
    assert zuordnung.quelle == "rueckfall"


def test_keine_betriebsseite_schlaegt_jedes_stichwort():
    """Meldet das Modell „kein Betrieb", gilt K6 — auch bei „Dachdecker" im Text.

    Sonst würde ein Blog über Dachdeckerei gegen den Maßstab eines
    Dachdeckerbetriebs gemessen.
    """
    zuordnung = klasse_fuer_branche("Blog über Dachdecker", betriebsseite=False)

    assert zuordnung.klasse == "K6"


def test_ohne_angabe_bleibt_es_beim_rueckfall():
    assert klasse_fuer_branche("", betriebsseite=True).klasse == "K1"
    assert klasse_fuer_branche(None, betriebsseite=True).klasse == "K1"


# ── Lücken sichtbar machen (§ 2.3 Schlussabsatz) ──────────────────────

def test_ein_nicht_zugeordneter_freitext_wird_vermerkt():
    """Ohne diese Spur wächst die Tabelle nie an den Stellen, wo sie fehlt."""
    nicht_zugeordnet.clear()

    klasse_fuer_branche("Alpaka-Zucht mit Wanderungen", betriebsseite=True)

    assert "alpaka-zucht mit wanderungen" in nicht_zugeordnet


def test_ein_zugeordneter_freitext_wird_nicht_vermerkt():
    nicht_zugeordnet.clear()

    klasse_fuer_branche("Dachdecker", betriebsseite=True)

    assert nicht_zugeordnet == set()
