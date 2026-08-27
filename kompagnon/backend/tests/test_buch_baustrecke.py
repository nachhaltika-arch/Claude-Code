# -*- coding: utf-8 -*-
"""
Die Buch-Baustrecke findet ihr Manuskript (BUCH-03, L-115).

**Warum ein Test ohne PDF.** Der Satz selbst braucht ReportLab und eine eigene
Umgebung (`buch/venv`); ihn in der CI mitlaufen zu lassen hieße, für jeden
Testlauf zweihundert Seiten zu setzen. Was hier geprüft wird, ist die Stelle,
an der es **stillschweigend** brechen würde: Wird eine Kapiteldatei umbenannt
oder verschoben, fehlt sie im Buch — und niemand sähe es, bis jemand das PDF
Seite für Seite durchgeht.

`buch/manuskript.py` kommt ohne ReportLab aus, damit genau dieser Test billig
bleibt.
"""
import importlib.util
import pathlib

import pytest

WURZEL = pathlib.Path(__file__).resolve().parents[3]
MODUL = WURZEL / "buch" / "manuskript.py"


def _manuskript():
    spec = importlib.util.spec_from_file_location("buch_manuskript", MODUL)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_die_baustrecke_liegt_im_repo():
    assert MODUL.exists(), (
        "buch/manuskript.py fehlt — dann gibt es keinen Weg vom Manuskript "
        "zum PDF, und BUCH-03 ist wieder offen.")


def test_alle_bestandteile_des_buchs_werden_gefunden():
    # Arrange
    m = _manuskript()

    # Act
    dateien = m.dateien()

    # Assert — Titelei, siebzehn Kapitel, vier Anhänge.
    assert len(dateien) == 22, [p.name for p in dateien]
    assert dateien[0].name == "TITELEI.md"
    assert dateien[1].name.startswith("KAPITEL-01-")
    assert dateien[-1].name.startswith("ANHANG-D-")


def test_das_arbeitsmaterial_steht_nicht_im_buch():
    """Redaktionelle Anmerkungen sind für Autor, Recht und Satz — nicht für den Leser."""
    m = _manuskript()
    kapitel = m.lesen(m.dateien()[1])
    assert "🔴" not in kapitel["text"], "eine offene Anmerkung steht noch im Buchtext"
    assert "Zuständigkeit" not in kapitel["text"]


def test_die_kopfdaten_werden_gelesen():
    m = _manuskript()
    kapitel = m.lesen(m.dateien()[1])
    assert kapitel["nummer"] == "1"
    assert kapitel["titel"] == "Die Website ist ein Betriebsmittel"
    assert kapitel["status"] == "entwurf"


@pytest.mark.parametrize("marke", ["[[UMBRUCH]]"])
def test_gesetzte_seitenumbrueche_ueberleben(marke):
    """`<!-- SEITENUMBRUCH -->` ist eine Satzanweisung, kein Kommentar."""
    m = _manuskript()
    zusammen = "".join(t["text"] for t in m.alles())
    assert zusammen.count(marke) >= 20, "die Umbruchmarken sind verlorengegangen"
