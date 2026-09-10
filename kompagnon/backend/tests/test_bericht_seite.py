# -*- coding: utf-8 -*-
"""Die Berichtsseite behauptet nichts, was nicht gemessen ist (L-191).

**Der Befund beim Einbauen des Entwurfs (10.09.2026).** Die Gestaltung kam
mit Beispielinhalt an Stellen, an denen Daten hingehoeren — und der
Beispielinhalt liest sich wie ein Befund ueber den Betrieb, der die Seite
bekommt. Gefunden wurden zwoelf solche Stellen, darunter:

* „Auf Ihrer Seite wurde kein Consent-Tool erkannt (0 von 4 Punkten, TDDDG)"
  — ein konkreter Mangel, den niemand gemessen hat.
* „Ihre Seite ist aelter als vier Jahre und in Teilen rechtlich offen."
* „25 % Rabatt fuer die ersten 25 Kunden" samt Code `WS25` — ein
  Preisversprechen, das der Katalog nicht kennt und die Kasse nicht einloest.
* „Erreicht das Abnahmeaudit nicht mindestens 96 Punkte…" — der
  Angebotsbaukasten sagt unter G1 **85**.
* „Branchenschnitt 64" und „Branchenschnitt aus 40 Betrieben derselben
  Branche, erhoben 01–08/2026" — es gibt keinen solchen Wert (L-190).
* „Quelle bitte ergaenzen — Zahl erst veroeffentlichen, wenn belegt" — eine
  Notiz des Entwerfenden an sich selbst.

Jede davon ist jetzt ein Feld oder ein Schalter, und **alle stehen auf aus**,
bis jemand sie mit Daten oder einer Entscheidung fuellt. Dieser Waechter
haelt das fest: Er rendert eine Seite ohne Einstellungen und prueft, dass
keine der Behauptungen darin steht.

**Warum am erzeugten Ergebnis und nicht an der Vorlage.** Ein Schalter, der
in der Vorlage steht und in den Daten fehlt, ist kein Schutz — er ist
Absicht ohne Wirkung. Geprueft wird die Seite, die der Kunde bekommt.
"""
import pytest

from services import bericht_seite


class _Db:
    """Ein Katalog ohne Produkte — der schlechteste Fall, nicht der beste."""

    def execute(self, *a, **k):
        class Ergebnis:
            def mappings(self_):
                class Zeile:
                    def first(self__):
                        return None
                return Zeile()
        return Ergebnis()

    def rollback(self):
        pass


class _Audit:
    company_name = "Muster GmbH"
    website_url = "https://muster.de"
    total_score = 61
    item_scores = {}
    item_sources = {}
    item_belege = {}
    coverage = 0
    blockers = "[]"
    erkannte_branche = ""
    branchenklasse = ""
    level = "Homepage Standard Bronze"


@pytest.fixture
def seite():
    return bericht_seite.rendern(_Db(), _Audit(), token="tok")


BEHAUPTUNGEN = [
    ("25 %", "Rabatt, den der Katalog nicht kennt"),
    ("WS25", "Rabattcode ohne Rabattfeld in der Kasse"),
    ("Rabattfeld", "Verweis auf ein Feld, das es nicht gibt"),
    ("96 Punkte", "Abnahmezusage, die G1 widerspricht"),
    ("Branchenschnitt", "Vergleichswert, den es nicht gibt (L-190)"),
    ("Quelle bitte", "Notiz des Entwerfenden"),
    ("älter als vier Jahre", "Urteil ueber die Seite des Kunden"),
    ("Consent-Tool erkannt (0 von 4", "erfundener Mangel"),
    ("Sprint-Plätze", "Aussage ueber die eigene Auslastung"),
    ("neovendo", "Name aus dem Beispiel"),
    ("03.09.2026", "Datum aus dem Beispiel"),
]


@pytest.mark.parametrize("text,warum", BEHAUPTUNGEN)
def test_keine_unbelegte_behauptung(seite, text, warum):
    assert text not in seite, f"{text!r} steht in der Seite — {warum}"


def test_die_seite_entsteht_ueberhaupt(seite):
    """Die positive Gegenprobe. Ohne sie waeren alle Pruefungen oben auch
    dann gruen, wenn gar keine Seite herauskommt."""
    assert len(seite) > 20000
    assert "Muster GmbH" in seite
    assert "61" in seite


def test_keine_vorlagenreste(seite):
    """Was der Erzeuger nicht kennt, faellt auf — statt beim Kunden zu stehen."""
    assert "<sc-" not in seite
    assert "{{" not in seite
    assert "image-slot" not in seite


def test_die_huelle_traegt_sprache_und_zeichensatz(seite):
    assert '<html lang="de">' in seite
    assert '<meta charset="utf-8">' in seite
    # Der Befund ueber eine fremde Website gehoert nicht in einen Index.
    assert 'name="robots" content="noindex' in seite


def test_ohne_produkt_kein_erfundener_preis(seite):
    """Der Katalog in dieser Probe ist leer. Dann steht dort **kein** Preis —
    ein Rueckfall auf einen Standardbetrag waere die teuerste Zeile der Datei."""
    assert "3.500" not in seite
    assert "4.165" not in seite
