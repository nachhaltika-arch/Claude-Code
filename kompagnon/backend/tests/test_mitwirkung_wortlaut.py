# -*- coding: utf-8 -*-
"""Steht der Mitwirkungskatalog im Code wortgleich im Angebot? (L-166)

**Die Textseite von L-166.** Der Katalog M1 bis M11 steht an zwei Orten: im
Angebotsbaukasten (`docs/Buch/Websprint Produkte/files/
KAS_00_Angebotsbaukasten.md` § A) und in `services/mitwirkung.py`. Der eine
ist das, was der Kunde unterschreibt; der andere das, was das System ihm
zeigt und woraus die Frist gerechnet wird.

**Warum ein Wächter und keine Sorgfalt.** Zwei Fassungen desselben Textes
laufen auseinander — das ist in diesem Projekt kein Verdacht, sondern
Erfahrung (L-27, L-29, L-105). Hier wiegt es schwerer als sonst: Weicht der
Wortlaut ab, zeigt das Konto eine Pflicht, die der Vertrag nicht kennt, oder
umgekehrt. Im Streit über die Bauzeitgarantie steht dann Aussage gegen
Vertrag.

**Was der Test nicht prüft.** Ob die Klausel juristisch trägt. Er prüft, ob
beide Fassungen dasselbe sagen — die eine Frage, die sich maschinell
beantworten lässt.
"""
import re
from pathlib import Path

import pytest

from services import mitwirkung as kat

BAUKASTEN = (Path(__file__).resolve().parents[3]
             / "docs" / "Buch" / "Websprint Produkte" / "files"
             / "KAS_00_Angebotsbaukasten.md")

WIRKUNG_IM_DOKUMENT = {
    "Fristbeginn": kat.FRISTBEGINN,
    "Fristpause": kat.FRISTPAUSE,
    "—": kat.OHNE_FRIST,
}


def _tabelle_aus_dem_baukasten():
    """Die Zeilen aus § A — Kürzel, Wortlaut, Fristrelevanz."""
    text = BAUKASTEN.read_text(encoding="utf-8")
    zeilen = {}
    for treffer in re.finditer(
            r"^\|\s*\*\*(M\d+)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$",
            text, re.M):
        kennung, wortlaut, wirkung = treffer.groups()
        # Die Hervorhebung im Dokument ist Auszeichnung, nicht Wortlaut.
        zeilen[kennung] = (wortlaut.replace("**", ""), wirkung.strip())
    return zeilen


def test_der_baukasten_liegt_da_wo_der_katalog_ihn_nennt():
    """Verschiebt jemand die Datei, muss dieser Test rot werden — nicht
    stillschweigend nichts mehr prüfen. Ein Wächter, der seinen Gegenstand
    nicht findet und trotzdem grün ist, ist keiner."""
    assert BAUKASTEN.exists(), f"Angebotsbaukasten nicht gefunden: {BAUKASTEN}"
    assert _tabelle_aus_dem_baukasten(), "§ A enthält keine lesbare M-Tabelle"


def test_beide_fassungen_kennen_dieselben_punkte():
    im_dokument = set(_tabelle_aus_dem_baukasten())
    im_code = {p.kennung for p in kat.KATALOG}

    assert im_dokument == im_code, (
        f"nur im Angebot: {sorted(im_dokument - im_code)} · "
        f"nur im Code: {sorted(im_code - im_dokument)}")


@pytest.mark.parametrize("kennung", [p.kennung for p in kat.KATALOG])
def test_der_vertragstext_steht_wortgleich_im_angebot(kennung):
    """`Punkt.vertragstext` ist ausdrücklich „der Wortlaut aus dem
    Angebotsbaukasten". Wenn er das nicht mehr ist, sagt das Kundenkonto
    etwas anderes als der unterschriebene Vertrag."""
    dokument = _tabelle_aus_dem_baukasten()
    wortlaut, _ = dokument[kennung]

    assert kat.NACH_KENNUNG[kennung].vertragstext == wortlaut


@pytest.mark.parametrize("kennung", [p.kennung for p in kat.KATALOG])
def test_die_fristwirkung_stimmt_mit_dem_angebot_ueberein(kennung):
    """**Die Spalte, an der die Garantie hängt.** Stünde M7 im Code als
    `FRISTBEGINN`, hielte eine ausstehende Bauplanfreigabe den Start auf,
    statt die laufende Frist ruhen zu lassen — zwei völlig verschiedene
    Zusagen, und die Oberfläche zeigte beide als „offen"."""
    _, wirkung = _tabelle_aus_dem_baukasten()[kennung]

    assert kat.NACH_KENNUNG[kennung].wirkung == WIRKUNG_IM_DOKUMENT[wirkung]
