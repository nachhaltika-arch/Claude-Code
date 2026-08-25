# -*- coding: utf-8 -*-
"""
Die erzeugten Tabellen im Manuskript müssen zum Katalog passen (BUCH-F3).

**Der Befund vom 25.08.2026.** Rund fünfzig Tabellen im Buch trugen die Zeile
„ERZEUGT aus `generiert/…` — nicht von Hand ändern". Die genannten Dateien gab
es nie, und kein Skript hat sie geschrieben. Zwei Angaben waren dadurch
nachweislich falsch: B4 stand als „abgeleitet" (seit S2.1 gemessen), D2 als
„Einschätzung" (seit S1.2 gemessen) — und Abschnitt 3.4 zählte 28/4/7 statt
30/3/6.

Ein Vermerk, der Pflege verbietet, ohne dass jemand pflegt, ist schlimmer als
gar keiner: Er hält jeden davon ab, hinzusehen.

Dieser Test schreibt nichts. Er lässt `scripts/buch-bloecke.py --pruefen`
laufen; das Skript meldet einen Rückgabewert ungleich null, sobald eine
erzeugte Tabelle vom Katalog abweicht **oder** eine handgepflegte
Abstufungstabelle einen Punktwert nennt, den es im Katalog nicht gibt.
"""
import pathlib
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parents[3]
SKRIPT = WURZEL / "scripts" / "buch-bloecke.py"


def test_das_skript_liegt_im_repo():
    assert SKRIPT.exists(), (
        "scripts/buch-bloecke.py fehlt — dann behaupten die Tabellen im "
        "Manuskript wieder, erzeugt zu sein, ohne dass jemand sie erzeugt."
    )


def test_die_tabellen_im_manuskript_entsprechen_dem_katalog():
    # Act
    lauf = subprocess.run([sys.executable, str(SKRIPT), "--pruefen"],
                          capture_output=True, text=True, cwd=WURZEL)

    # Assert
    assert lauf.returncode == 0, (
        "Eine Tabelle im Buchmanuskript weicht vom Kriterienkatalog ab. "
        "Neu erzeugen mit `python3 scripts/buch-bloecke.py`.\n\n"
        + lauf.stdout + lauf.stderr
    )


def test_die_punktwerte_der_handtabellen_werden_wirklich_nachgerechnet():
    """Ein Wächter, der nichts mehr findet, meldet auch nichts mehr.

    Genau das ist beim zweiten Probelauf passiert: Nachdem das Skript die
    falschen Vermerke berichtigt hatte, erkannte sein eigener Ausdruck die
    Marken nicht mehr wieder — und meldete zufrieden „0 Abweichungen", ohne
    noch eine einzige Tabelle anzusehen.
    """
    lauf = subprocess.run([sys.executable, str(SKRIPT), "--pruefen"],
                          capture_output=True, text=True, cwd=WURZEL)
    zeile = [z for z in lauf.stdout.splitlines() if "nachgerechnet" in z]
    assert zeile, lauf.stdout
    anzahl = int(zeile[0].split()[0])
    assert anzahl >= 30, f"nur {anzahl} Tabellen nachgerechnet — {zeile[0]}"


# ── Zahlen im Fließtext, die keine Marke tragen (B3.2.5) ─────────────

def _manuskript(name: str) -> str:
    pfad = (WURZEL / "docs" / "Buch" / "Buch - Kompagnon - Homepage Standard v2"
            / "Vollständige dokumentation Buch V2" / name)
    assert pfad.exists(), pfad
    return pfad.read_text(encoding="utf-8")


def test_die_klassenmaxima_im_glossar_stimmen_mit_dem_katalog():
    """Der einzige Zahlensatz des Glossars — im Buch als Drift-Kandidat markiert.

    Er steht in einem Satz und trägt keine Marke, also erzeugt ihn kein
    Skript. Prüfen lässt er sich trotzdem: Die Zahlen folgen aus dem Katalog.
    """
    import sys

    sys.path.insert(0, str(WURZEL / "kompagnon" / "backend"))
    from services.audit_criteria import anwendbares_maximum

    glossar = _manuskript("ANHANG-A-Glossar.md")
    eintrag = [z for z in glossar.splitlines()
               if z.startswith("**Anwendbares Maximum**")]
    assert eintrag, "der Eintrag fehlt"

    voll = anwendbares_maximum("K1")
    assert f"{voll} für K1" in eintrag[0], eintrag[0]
    assert f"{anwendbares_maximum('K4')} für K4" in eintrag[0]
    assert f"{anwendbares_maximum('K6')} für K6" in eintrag[0]


def test_die_punktkette_des_fallbeispiels_geht_auf():
    """Die zweite Kontrollrechnung des Buchs (B3.2.2), nachgerechnet.

    76 → 81 → 90 → 93 → 96 Rohpunkte gegen 74 → 79 → 87 → 90 → 93. Wer eine
    Kategorie im Buch ändert, ändert diese Kette mit — und merkt es hier.
    """
    kette = [(76, 74), (81, 79), (90, 87), (93, 90), (96, 93)]
    for roh, erwartet in kette:
        assert round(roh / 103 * 100) == erwartet, (roh, erwartet)

    plan = _manuskript("KAPITEL-15-Der-30-Tage-Plan.md")
    for roh, wert in kette:
        assert f"| {roh} |" in plan, f"Rohpunktzahl {roh} fehlt in 15.7"


def test_bis_platin_fehlen_zwei_punkte_nicht_sieben():
    """Der Befund vom 25.08.2026.

    Das Kapitel sagte „Bis Platin fehlen sieben Punkte". Sieben ist der
    Abstand zum **Höchstwert** 103; bis Platin sind es zwei — 98 Rohpunkte
    ergeben 95. Auf dieser Zahl steht das ganze Argument, Platin nicht mehr
    anzustreben.
    """
    assert round(98 / 103 * 100) == 95, "Platin ab 95 — 98 Rohpunkte genügen"
    assert round(97 / 103 * 100) == 94, "97 Rohpunkte genügen noch nicht"

    plan = _manuskript("KAPITEL-15-Der-30-Tage-Plan.md")
    assert "bis Platin nur zwei" in plan
    assert "Bis Platin fehlen sieben Punkte" not in plan
