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
