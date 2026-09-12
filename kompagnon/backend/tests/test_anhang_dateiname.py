# -*- coding: utf-8 -*-
"""Der Dateiname eines Anhangs muss durch eine ASCII-Kopfzeile passen.

**Gefunden am 12.09.2026 beim Durchlaufen des Trichters**, nicht durch einen
Test — der Bericht eines Betriebs mit Umlaut im Namen kam so heraus:

    content-disposition: attachment;
      filename="Website-Analyse-Das-Ingenieurb\\xfcro-f\\xfcr-nachhaltige-Wirtschaft.pdf"

Das Byte ``0xfc`` ist ein Latin-1-``ü`` in einem Feld, das nach RFC 7230 nur
ASCII tragen darf. Ein Client, der UTF-8 erwartet — und das tun die meisten —
sieht dort ein ungültiges Byte und setzt ein Ersatzzeichen. Der Kunde bekommt
eine Datei mit kaputtem Namen, und zwar **ausgerechnet** der Kunde, dessen
Firmenname deutsch geschrieben ist. In der Startbranche heißt das jeder
zweite: „Sanitär" trägt selbst ein ä.

**Warum nicht einfach Umlaute wegwerfen.** Weil der Name dann falsch ist
statt kaputt, und weil RFC 6266 den richtigen Weg längst kennt: ``filename``
bleibt als ASCII-Rückfall für alte Clients stehen, ``filename*=UTF-8''…``
trägt den echten Namen. Moderne Browser nehmen den zweiten.

**Der zweite Grund ist Sicherheit.** ``company_name`` kommt aus dem Scraper,
also von einer fremden Seite. Ein Anführungszeichen darin beendet die
Zeichenkette, ein Zeilenumbruch beginnt eine neue Kopfzeile. Beides gehört
entfernt, bevor es in eine Kopfzeile geschrieben wird.
"""
from pathlib import Path
from urllib.parse import unquote

import pytest

from services.dateinamen import anhang_kopfzeile


def _ascii_rein(wert: str) -> bool:
    try:
        wert.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


class TestAsciiRein:
    """Die Abwesenheitszusicherung — und daneben eine positive."""

    def test_umlaute_verlassen_die_kopfzeile_nicht_als_rohbyte(self):
        wert = anhang_kopfzeile("Website-Analyse-Ingenieurbüro.pdf")
        assert _ascii_rein(wert)

    def test_der_echte_name_steht_trotzdem_darin(self):
        """Ohne diese Prüfung wäre „alles weggeworfen" auch grün."""
        wert = anhang_kopfzeile("Website-Analyse-Ingenieurbüro.pdf")
        stern = wert.split("filename*=UTF-8''", 1)[1]
        assert unquote(stern, encoding="utf-8") == "Website-Analyse-Ingenieurbüro.pdf"

    def test_beide_formen_stehen_da(self):
        wert = anhang_kopfzeile("Bericht-Sanitär.pdf")
        assert 'filename="' in wert
        assert "filename*=UTF-8''" in wert


class TestRueckfall:
    """Der ASCII-Rückfall soll lesbar sein, nicht nur gültig."""

    @pytest.mark.parametrize("eingabe,erwartet", [
        ("Ingenieurbüro.pdf", "Ingenieurbuero.pdf"),
        ("Sanitär-Müller.pdf", "Sanitaer-Mueller.pdf"),
        ("Straße.pdf", "Strasse.pdf"),
        ("Öko-Ärzte.pdf", "Oeko-Aerzte.pdf"),
    ])
    def test_deutsche_umlaute_werden_umschrieben(self, eingabe, erwartet):
        wert = anhang_kopfzeile(eingabe)
        assert f'filename="{erwartet}"' in wert

    def test_was_sich_nicht_umschreiben_laesst_faellt_weg(self):
        wert = anhang_kopfzeile("Bericht-日本.pdf")
        assert _ascii_rein(wert)
        assert 'filename="Bericht-.pdf"' in wert

    def test_ein_name_ganz_ohne_ascii_bekommt_einen_ersatz(self):
        """Ein leerer Dateiname ist kein Dateiname."""
        wert = anhang_kopfzeile("日本.pdf")
        assert 'filename="Datei.pdf"' in wert
        assert unquote(wert.split("filename*=UTF-8''", 1)[1]) == "日本.pdf"


class TestKopfzeilenEinschleusung:
    """`company_name` kommt aus dem Scraper — also von einer fremden Seite."""

    def test_anfuehrungszeichen_beenden_die_zeichenkette_nicht(self):
        wert = anhang_kopfzeile('Firma".pdf')
        assert wert.count('"') == 2

    def test_zeilenumbruch_beginnt_keine_neue_kopfzeile(self):
        wert = anhang_kopfzeile("Firma\r\nX-Beliebig: ja.pdf")
        assert "\r" not in wert and "\n" not in wert

    def test_rueckstrich_maskiert_nichts(self):
        wert = anhang_kopfzeile('Firma\\".pdf')
        assert "\\" not in wert


class TestAsciiBleibtWieBisher:
    def test_ein_reiner_ascii_name_steht_unveraendert_im_rueckfall(self):
        wert = anhang_kopfzeile("Website-Analyse-Muster-GmbH.pdf")
        assert wert.startswith('attachment; filename="Website-Analyse-Muster-GmbH.pdf"')


ROUTER = Path(__file__).resolve().parent.parent / "routers"


class TestKeinHandbau:
    """Der Wächter: Die Kopfzeile wird nirgends mehr von Hand gebaut.

    **Elf Stellen bauten sie selbst, vier davon aus Daten.** Ein Fehler, der
    an vier Orten steht, ist keiner, den man an einem Ort repariert — er
    kommt am fünften zurück, sobald jemand einen neuen Endpunkt schreibt und
    beim Nachbarn abschaut. Deshalb prüft das hier den ganzen Ordner.

    `services/email.py` bleibt bewusst draußen: Dort geht es um eine
    MIME-Kopfzeile in einer E-Mail, und die Python-Bibliothek kodiert sie
    nach RFC 2231 selbst. Eine HTTP-Kopfzeile tut das nicht.
    """

    def test_keine_datei_baut_die_kopfzeile_selbst(self):
        schuldige = [p.name for p in ROUTER.glob("*.py")
                     if "attachment; filename" in p.read_text(encoding="utf-8")]
        assert schuldige == [], (
            "Diese Endpunkte bauen den Anhangsnamen von Hand statt über "
            f"anhang_kopfzeile(): {schuldige}")

    def test_und_der_helfer_wird_wirklich_benutzt(self):
        """Ohne diese Prüfung wäre auch „gar keine Downloads mehr" grün."""
        nutzer = [p.name for p in ROUTER.glob("*.py")
                  if "anhang_kopfzeile" in p.read_text(encoding="utf-8")]
        assert len(nutzer) >= 10, f"nur {len(nutzer)} Aufrufer gefunden: {nutzer}"

    def test_der_widget_bericht_ist_darunter(self):
        """Die Stelle, an der der Fehler am 12.09. aufgefallen ist."""
        quelle = (ROUTER / "widget.py").read_text(encoding="utf-8")
        assert "anhang_kopfzeile(f\"Website-Analyse-{name}.pdf\")" in quelle
