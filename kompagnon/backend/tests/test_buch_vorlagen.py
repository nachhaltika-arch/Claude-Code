# -*- coding: utf-8 -*-
"""
Die Vorlagen 1 und 2 halten ihre Zusage „eine Seite" (B6.2).

**Zwei Befunde vom 25.08.2026, beide erst im PDF sichtbar:**

1. **Die Ankreuzkästchen fehlten.** Das Manuskript benutzt 89-mal `☐` — Noto
   Sans enthält weder dieses noch ein anderes Kästchen-Zeichen, und ReportLab
   verschluckt ein fehlendes Zeichen stillschweigend. In den fünf Vorlagen und
   im Selbsttest blieben Lücken. Ein Ergebnisblatt ohne Kästchen ist kein
   Formular.
2. **Vorlage 1 lief über.** Nicht am Inhalt — der belegt 484 von 539 Punkt —,
   sondern am Luftraum zwischen den Blöcken.

Dieser Test prüft, was ohne Satzlauf prüfbar ist. Die Seitenzahl selbst misst
`buch/bauen.py`; sie hier nachzubauen hieße, den Satz zweimal zu haben.
"""
import pathlib

import pytest

WURZEL = pathlib.Path(__file__).resolve().parents[3]
ANKREUZEN = WURZEL / "buch" / "ankreuzen.py"
ANHANG_C = (WURZEL / "docs" / "Buch" / "Buch - Kompagnon - Homepage Standard v2"
            / "Vollständige dokumentation Buch V2" / "ANHANG-C-Fuenf-Vorlagen.md")


def test_die_schrift_kennt_kein_kaestchen():
    """Der Grund, warum gezeichnet wird — festgehalten, nicht erinnert.

    Sollte eine spätere Schriftfassung die Zeichen mitbringen, schlägt dieser
    Test an, und jemand entscheidet bewusst, ob weiter gezeichnet wird.
    """
    fonttools = pytest.importorskip("fontTools.ttLib")

    schrift = fonttools.TTFont(WURZEL / "assets" / "schriften" / "NotoSans-Regular.ttf")
    tabelle = schrift.getBestCmap()

    for zeichen in "☐□▢◻":
        assert ord(zeichen) not in tabelle, (
            f"{zeichen} ist jetzt in der Schrift — gezeichnete Kästchen prüfen")


def test_die_kaestchen_werden_gezeichnet():
    """Ein Zeichen, das die Schrift nicht kennt, darf nicht still verschwinden."""
    quelle = ANKREUZEN.read_text(encoding="utf-8")

    assert "c.rect(" in quelle, "die Kästchen werden nicht gezeichnet"
    assert "KAESTCHEN" in quelle


def test_der_setzer_erkennt_kaestchen_in_text_und_tabelle():
    """Beides kommt vor: „☐ Selbsttest" steht in einer Tabellenzelle,
    „☐ Platin (95–100)" als eigener Absatz."""
    inhalt = (WURZEL / "buch" / "inhalt.py").read_text(encoding="utf-8")

    assert inhalt.count("enthaelt_kaestchen") >= 2, (
        "Kästchen werden nur an einer der beiden Stellen erkannt")


def test_die_vorlagen_versprechen_eine_seite():
    """Die Zusage steht im Manuskript — sie ist der Maßstab für B6.2."""
    text = ANHANG_C.read_text(encoding="utf-8")

    for vorlage in ("Vorlage 1", "Vorlage 2"):
        block = text.split(f"## {vorlage}")[1][:400]
        assert "Eine Seite" in block, f"{vorlage} nennt ihre Zusage nicht mehr"


def test_der_formularsatz_ist_enger_als_der_fliesstext():
    """Ohne ihn braucht Vorlage 1 zwei Seiten — mit ihm eine."""
    stile = (WURZEL / "buch" / "stile.py").read_text(encoding="utf-8")

    assert "formularabschnitt" in stile and "formular" in stile
    inhalt = (WURZEL / "buch" / "inhalt.py").read_text(encoding="utf-8")
    assert "self.kompakt" in inhalt
