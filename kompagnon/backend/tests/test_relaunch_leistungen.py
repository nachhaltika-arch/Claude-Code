# -*- coding: utf-8 -*-
"""Der Leistungsumfang von Relaunch und Check PLUS (Vorgabe David, 10.09.2026).

**Warum das ein eigener Waechter ist.** Die Liste steht an zwei Stellen im
Code — der Vorlage in `startphase.py` und der Migration —, und aus ihr
speisen sich die Kasse, die Auftragsbestaetigung und seit dem 10.09. der
Leistungsumfang auf der Berichtsseite. Sie ist damit kein Anzeigetext,
sondern das, was zugesagt wird. Ein stiller Unterschied zwischen den beiden
Stellen hiesse: Eine frisch aufgesetzte Datenbank verspricht etwas anderes
als eine gewachsene — genau die Klasse, die `test_produktvorlage` fuer die
Paketmenge schon abdeckt, hier fuer den Inhalt.

**Gepruefte Eigenschaften, nicht nur Vorhandensein.** Die Zahl der Punkte
ist Teil der Zusage: Wer eine Zeile ergaenzt oder streicht, aendert den
Vertragsgegenstand und soll hier vorbeikommen.
"""
import pytest

from startphase import produkt_vorlage

#: Wortlaut nach Vorgabe David vom 10.09.2026.
LEISTUNGEN = [
    "Eingangsaudit nach Homepage-Standard, 100 Punkte in 8 Kategorien",
    "Strukturabgleich und Seitenplan auf Basis Ihrer bestehenden Website",
    "Aufbau im KOMPAGNON-Komponentensystem, responsiv, bis 6 Seiten",
    "Übernahme und redaktionelle Überarbeitung Ihrer Texte",
    "Aufbereitung Ihres Bildmaterials, bis 30 Bilder, inkl. Alternativtexte",
    "Kontaktformular mit Spam-Schutz und Empfangsbestätigung",
    "Einbindung Ihrer Rechtstexte",
    "Grundlagen der Barrierefreiheit: Kontraste, Tastatur, Semantik",
    "Technische Grundoptimierung und strukturierte Auszeichnung",
    "Hosting, SSL, Weiterleitungen, Umstellung der Domain",
    "Abnahmeaudit mit schriftlichem Protokoll je Kategorie",
    "Einweisung, 30 Minuten, und Übergabe aller Zugänge",
]


@pytest.fixture
def eintrag():
    treffer = [p for p in produkt_vorlage() if p["slug"] == "websprint_relaunch"]
    assert len(treffer) == 1
    return treffer[0]


def test_die_vorlage_traegt_genau_diese_liste(eintrag):
    assert eintrag["features"] == LEISTUNGEN


def test_die_migration_traegt_dieselbe(eintrag):
    """Beide Stellen oder keine — sonst haengt die Zusage davon ab, wie die
    Datenbank entstanden ist."""
    import pathlib

    quelle = (pathlib.Path(__file__).resolve().parent.parent
              / "migrations_runtime.py").read_text(encoding="utf-8")
    fehlend = [z for z in LEISTUNGEN if z not in quelle]
    assert fehlend == [], f"in der Migration nicht gefunden: {fehlend}"


def test_die_zahl_der_zusagen_ist_teil_der_zusage(eintrag):
    assert len(eintrag["features"]) == 12


#: Wortlaut nach Vorgabe David vom 10.09.2026.
#:
#: **Position 3 ist eine Zusage ohne Werkzeug.** „Wettbewerbsvergleich mit
#: drei Betrieben aus dem Umkreis, je mit Punktzahl" verlangt drei weitere
#: Analysen je Verkauf; einen Vergleichswert je Branche gibt es im System
#: nicht (L-190). Am 10.09.2026 ausdruecklich entschieden: Die Zeile bleibt.
#: Sie ist damit **Handarbeit im Auswertungsgespraech**, nicht etwas, das
#: der Bericht mitliefert — und dieser Kommentar steht hier, damit niemand
#: sie fuer eine gebaute Auswertung haelt.
CHECK_PLUS = [
    "Vollständiges Audit, manuell nachgeprüft",
    "Manuelle Bewertung der nicht maschinell prüfbaren Punkte: "
    "Verständlichkeit der Leistungsdarstellung, Erkennbarkeit der Kontaktwege, "
    "Passung zur Zielgruppe",
    "Wettbewerbsvergleich mit drei Betrieben aus dem Umkreis, je mit Punktzahl",
    "Priorisierte Maßnahmenliste: was zuerst, welcher Punktgewinn, welcher Aufwand",
    "Auswertungsgespräch, 60 Minuten, per Videokonferenz",
    "Schriftliche Zusammenfassung mit Handlungsempfehlung",
]


@pytest.fixture
def check_plus():
    treffer = [p for p in produkt_vorlage() if p["slug"] == "check_plus"]
    assert len(treffer) == 1
    return treffer[0]


def test_check_plus_traegt_genau_diese_liste(check_plus):
    assert check_plus["features"] == CHECK_PLUS


def test_check_plus_in_der_migration():
    import pathlib

    quelle = (pathlib.Path(__file__).resolve().parent.parent
              / "migrations_runtime.py").read_text(encoding="utf-8")
    fehlend = [z for z in CHECK_PLUS if z not in quelle]
    assert fehlend == [], f"in der Migration nicht gefunden: {fehlend}"


def test_der_wettbewerbsvergleich_steht_ausdruecklich_drin(check_plus):
    """Er ist die teuerste Zeile der Liste — drei Analysen je Verkauf, von
    Hand. Wer sie streicht, aendert den Vertragsgegenstand und soll hier
    vorbeikommen."""
    assert any("Wettbewerbsvergleich" in z for z in check_plus["features"])
