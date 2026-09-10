# -*- coding: utf-8 -*-
"""Die Trichter-Vorschau baut jede Ansicht — und zeigt keine Innereien.

**Warum das ein Test ist und nicht nur ein Werkzeug.** Die Vorschau
(`scripts/trichter-vorschau.py`) rendert dieselben Erzeugnisse, die ein
Kunde bekommt: Widget, Berichtsseite, die drei Mails. Wenn eine davon
abstürzt oder Datenbankinhalt durchreicht, ist das kein Fehler der
Vorschau — es ist ein Fehler, den der Kunde sehen würde.

Genau so wurde am 10.09.2026 gefunden, dass die neue Berichtsseite die
Kennungen der K.-o.-Kriterien ungeübersetzt anzeigte: Im roten Kasten stand
`kein_impressum. keine_datenschutzerklaerung.` statt der Sätze aus
`BLOCKER_LABELS`. Der Fund kam aus dem Hinsehen, nicht aus einem Test —
deshalb steht er jetzt in einem.

**Was hier NICHT geprüft wird.** Ob die Ansichten richtig aussehen. Ein
Test kann sagen, dass eine Seite gebaut wurde und keine Python-Darstellung
enthält; ob der Kasten an der richtigen Stelle sitzt, sieht nur ein Mensch.
"""
import importlib.util
import json
import os
import re

import pytest

SKRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                      "scripts", "trichter-vorschau.py")


@pytest.fixture(scope="module")
def vorschau():
    spec = importlib.util.spec_from_file_location("trichter_vorschau", SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


#: Wie eine durchgereichte Python-Darstellung aussieht.
#:
#: **Die maskierte Form gehört dazu.** Die Berichtsvorlage escapt jeden
#: Wert, den sie einsetzt — ein durchgereichtes Wörterbuch steht im
#: Quelltext deshalb als `{&#x27;titel&#x27;: …}` und erst im Browser als
#: `{'titel': …}`. Ein Muster, das nur nach `{'` sucht, findet den Fehler
#: genau dort nicht, wo er auftrat. (Beim ersten Schreiben dieses Tests
#: passiert, gemerkt beim Nachrechnen.)
#:
#: `&#x27;: ` allein wäre zu grob: Der Katalog führt ein Kriterium
#: „Lighthouse-Audit 'font-size'", und das ist keine Innerei, sondern der
#: Name der Prüfung.
INNEREIEN = re.compile(
    r"""\{['"]|\{&\#x27;|\[\{['"]|\[\{&\#x27;|<sqlalchemy|object at 0x""")


def _alle_ansichten(vorschau):
    # Die Landingpage ist ein fertiger Export ohne Vorlagensprache — sie
    # wird ausgeliefert, nicht gebaut, und hat deshalb hier nichts zu prüfen.
    return [a for a in vorschau.ANSICHTEN if a["schluessel"] != "landingpage"]


def test_es_gibt_jede_stufe_des_trichters(vorschau):
    """Fehlt eine Ansicht, prüft niemand sie mehr — und niemand merkt es."""
    schluessel = {a["schluessel"] for a in vorschau.ANSICHTEN}
    assert schluessel == {
        "landingpage", "widget", "teaser", "mail-bestaetigung",
        "mail-bericht", "bericht", "mail-erinnerung",
    }


@pytest.mark.parametrize("regler", [
    {},
    {"punkte": "34"},
    {"punkte": "88"},
    {"punkte": "61", "rabatt": "an", "abnahme": "85",
     "knappheit": "an", "kaufwege": "an"},
])
def test_jede_ansicht_baut(vorschau, regler):
    for ansicht in _alle_ansichten(vorschau):
        seite = ansicht["bauer"](regler)
        assert seite, ansicht["schluessel"]
        assert len(seite) > 500, f"{ansicht['schluessel']} ist verdächtig kurz"


@pytest.mark.parametrize("regler", [
    {}, {"punkte": "34"},
    {"punkte": "61", "rabatt": "an", "abnahme": "85", "knappheit": "an"},
])
def test_keine_ansicht_zeigt_innereien(vorschau, regler):
    """Der Fund vom 10.09.2026, als Wächter.

    Die Berichtsseite zeigte Kennungen aus der Datenbank. Dieselbe Klasse
    hatte kurz zuvor der Leistungsumfang (Python-Wörterbücher statt Text)
    und der Deckungsgrad (`true` statt eines Satzes).
    """
    for ansicht in _alle_ansichten(vorschau):
        text = ansicht["bauer"](regler).decode("utf-8", "replace")
        treffer = INNEREIEN.search(text)
        assert not treffer, (
            f"{ansicht['schluessel']} zeigt {treffer.group()!r} — "
            f"Kontext: {text[max(0, treffer.start() - 90):treffer.end() + 90]!r}")


def test_die_kopfzahl_ist_die_summe_der_einzelwertungen(vorschau):
    """Sonst widerspricht der Bericht sich selbst.

    Oben steht die Gesamtpunktzahl, unten die Kategorien. Sind das zwei
    verschiedene Rechnungen, weiß niemand, welche gilt — und ein Kunde,
    der nachzählt, findet einen Fehler, den es nicht gibt.
    """
    for ziel in (34, 61, 80, 88):
        befund = vorschau.Audit(ziel)
        assert sum(befund.item_scores.values()) == befund.total_score


def test_eine_hohe_punktzahl_bringt_ihre_abdeckung_mit(vorschau):
    """Bei 78 % erhobenen Kriterien sind höchstens 80 Punkte erreichbar.

    Das ist kein Zufall der Vorschau, sondern der Produktivzustand (L-165):
    Solange die Performance-Werte fehlen, ist die Abnahmezusage über 85
    Punkte rechnerisch unerreichbar. Die Vorschau soll das **nicht**
    verdecken, indem sie eine Zahl zeigt, die der Befund nicht trägt.
    """
    niedrig = vorschau.Audit(61)
    hoch = vorschau.Audit(88)
    assert niedrig.coverage < 100
    assert hoch.coverage == 100
    assert hoch.total_score == 88


def test_die_wertungen_benutzen_die_schluessel_des_katalogs(vorschau):
    """Die erste Fassung erfand `impressum_vorhanden`; der Katalog führt
    `rc_impressum`. Damit fand die Berichtsseite zu keinem Kriterium etwas,
    und die Vorschau zeigte eine hohle Seite, die nichts prüfte."""
    from services.audit_criteria import all_criteria

    echte = {k.key for k in all_criteria()}
    befund = vorschau.Audit(61)
    assert befund.item_scores
    assert set(befund.item_scores) <= echte


def test_die_blocker_sind_kennungen_und_keine_saetze(vorschau):
    """Sonst prüft die Vorschau die Übersetzung nicht mit."""
    from services.audit_criteria import BLOCKING_CRITICAL, BLOCKING_MAJOR

    assert set(vorschau.BLOCKER) <= (BLOCKING_CRITICAL | BLOCKING_MAJOR)


def test_der_katalog_kommt_aus_der_startphase(vorschau):
    """Preise stehen an einer Stelle (L-29). Eine Vorschau mit eigenen
    Zahlen zeigt ein Angebot, das es nicht gibt."""
    zeilen = vorschau.katalog()
    assert zeilen["websprint_relaunch"]["price_netto"] == 3500.00
    assert zeilen["check_plus"]["price_netto"] == 249.00


def test_der_waechter_wuerde_ein_durchgereichtes_woerterbuch_finden(vorschau):
    """Gegenprobe. Ein Wächter, der nie anschlägt, bewacht nichts.

    **Nicht über die Blocker.** Der erste Versuch stellte den Fehler vom
    10.09.2026 nach, indem er Wörterbücher in `blockers` legte — und der
    Wächter schwieg. Zu Recht: Die Reparatur desselben Tages fängt
    Wörterbücher in `_rechtsbefund` ab und holt sich `titel` heraus. Der
    Weg ist zu, und ein Test, der ihn benutzt, prüft nur noch die Reparatur.

    Offen ist der Leistungsumfang: Die Vorlage schreibt `{{ l }}`, also die
    Zeichenkette selbst. Steht im Katalog statt eines Satzes ein Wörterbuch,
    landet dessen Python-Darstellung auf der Verkaufsseite — genau das ist
    am 10.09.2026 schon einmal passiert.
    """
    from services import bericht_seite

    class KatalogMitWoerterbuch(vorschau.KatalogDb):
        def __init__(self):
            super().__init__()
            zeile = dict(self.zeilen["websprint_relaunch"])
            zeile["features"] = [{"name": "Eingangsaudit", "punkte": 100}]
            self.zeilen = {**self.zeilen, "websprint_relaunch": zeile}

    seite = bericht_seite.rendern(
        KatalogMitWoerterbuch(), vorschau.Audit(61),
        token="probe", einstellungen={})
    assert INNEREIEN.search(seite), (
        "Der Wächter erkennt ein durchgereichtes Wörterbuch nicht — "
        "er hätte den Fehler vom 10.09.2026 durchgelassen.")


def test_der_waechter_haelt_echte_kriterienbezeichnungen_aus(vorschau):
    """Gegenrichtung: Er darf nicht bei jedem Apostroph anschlagen.

    Der Katalog führt „Lighthouse-Audit 'font-size'". Ein Wächter, der
    daran scheitert, wird nach dem dritten Fehlalarm abgeschaltet.
    """
    assert not INNEREIEN.search(
        "Lighthouse-Audit &#x27;font-size&#x27;: lesbare Schriftgröße")
    assert not INNEREIEN.search("Ein Satz mit { geschweifter Klammer }")
