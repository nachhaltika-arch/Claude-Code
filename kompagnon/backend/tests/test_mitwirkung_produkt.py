# -*- coding: utf-8 -*-
"""Die Mitwirkungspunkte richten sich nach dem gekauften Produkt (L-168).

**Der Befund vom 07.09.2026.** `Punkt` traegt seit jeher ein Feld `produkte`
mit dem Kommentar „Leere Menge heisst: gilt fuer jedes Produkt". Kein einziger
Punkt setzte es, und `gilt_fuer` las es nie — ein totes Feld mit dokumentierter
Bedeutung. Jedes Projekt bekam dieselben elf Punkte.

**Warum das mehr ist als Kosmetik.** M6 (Positionierungsgespraech) traegt
`FRISTBEGINN`. Ein Websprint Start konnte seine Bauzeit-Uhr also erst starten,
wenn ein Gespraech stattgefunden hat, das sein Vertrag gar nicht enthaelt —
Abgrenzung A18 schliesst persoenliche Termine und Telefonberatung sogar
ausdruecklich aus. An dieser Uhr haengt die Verzugspauschale (L-166).

**Und der Fehler ging in beide Richtungen.** Der Lagebild-Eintrag vermutete,
bei den drei grossen Websprints falle nichts auf, „ihre M-Listen sind aehnlich
genug". Nachgezaehlt an den Datenblaettern stimmt das nicht: Relaunch hat
ebenfalls kein M6/M7/M8, und Neubau und System haben kein M2 — dort schreiben
wir die Texte selbst. Betroffen waren alle vier Produkte.

Die Zuordnung unten ist aus den Kopfzeilen der Datenblaetter abgeschrieben,
nicht hergeleitet.
"""
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))

import pytest

from services import mitwirkung as kat

#: Wortlaut der Zeile „| Mitwirkung |" im jeweiligen Datenblatt.
#: Bedingte Punkte (M9 Migration, M10 Karriereseite) stehen hier **nicht** —
#: sie haengen am Projekt, nicht am Produkt, und werden weiter ueber
#: `bedingung` geregelt. M11 (Rechnungsdaten) steht in keiner Kopfzeile und
#: gilt ueberall: ohne Rechnungsdaten keine Rechnung.
LAUT_DATENBLATT = {
    "websprint_start":    {"M1", "M2", "M3", "M4", "M5"},
    "websprint_relaunch": {"M1", "M2", "M3", "M4", "M5"},
    "websprint_neubau":   {"M1", "M3", "M4", "M5", "M6", "M7", "M8"},
    "websprint_system":   {"M1", "M3", "M4", "M5", "M6", "M7", "M8"},
}

IMMER = {"M11"}


@pytest.mark.parametrize("produkt,erwartet", sorted(LAUT_DATENBLATT.items()))
def test_die_punkte_entsprechen_dem_datenblatt(produkt, erwartet):
    kennungen = {p.kennung for p in kat.gilt_fuer(set(), produkt=produkt)}
    assert kennungen == erwartet | IMMER


def test_ohne_produkt_gilt_weiter_alles():
    """Ein Projekt ohne Paketangabe darf nicht stillschweigend leer laufen.

    Der Fehler soll in die sichtbare Richtung fallen: lieber ein Punkt zu
    viel, den jemand wegklickt, als ein fehlender, den niemand bemerkt.
    """
    ohne = {p.kennung for p in kat.gilt_fuer(set(), produkt=None)}
    assert "M6" in ohne and "M2" in ohne


def test_bedingte_punkte_haengen_weiter_am_projekt():
    """M9 und M10 kommen aus dem Projekt, nicht aus dem Produkt."""
    mit = {p.kennung for p in kat.gilt_fuer({"migration"}, produkt="websprint_neubau")}
    assert "M9" in mit
    ohne = {p.kennung for p in kat.gilt_fuer(set(), produkt="websprint_neubau")}
    assert "M9" not in ohne


def test_start_und_relaunch_starten_ohne_positionierungsgespraech():
    """Der eigentliche Schaden — an dieser Uhr haengt die Verzugspauschale.

    M6 traegt `FRISTBEGINN`. Solange es fuer jedes Produkt galt, hielt es die
    Frist von Projekten auf, deren Vertrag das Gespraech nicht kennt.
    """
    for produkt in ("websprint_start", "websprint_relaunch"):
        punkte = kat.gilt_fuer(set(), produkt=produkt)
        offen = {p.kennung for p in kat.fristbeginn_offen(punkte, erledigt=())}
        assert "M6" not in offen, produkt


def test_jedes_katalogprodukt_ist_zugeordnet():
    """Ein neues Produkt erzwingt eine Entscheidung, statt still durchzufallen.

    Ohne diesen Waechter waere die Zuordnung eine Liste, die beim naechsten
    Produkt vergessen wird — und das neue Produkt bekaeme wortlos den falschen
    Satz Punkte. Bauleistungen sind hier gemeint; Buch, Workbook und Check
    haben keine Mitwirkung im Sinne des Bauvertrags.
    """
    from startphase import produkt_vorlage

    baut = {e["slug"] for e in produkt_vorlage()
            if str(e["slug"]).startswith("websprint_")}
    assert baut, "keine Bauprodukte im Katalog gefunden — Waechter ohne Gegenstand"
    fehlend = baut - set(kat.PRODUKT_PUNKTE)
    assert not fehlend, (
        f"Diese Produkte haben keine Mitwirkungszuordnung: {sorted(fehlend)}. "
        f"Die Liste steht in der Kopfzeile ihres Datenblatts.")
