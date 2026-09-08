# -*- coding: utf-8 -*-
"""Die Facebook-Pixel-ID des Widgets (Wunsch David, 08.09.2026).

**Warum als Einstellung und nicht fest in der Datei.** Das Widget liegt als
statische Datei auf fremden Seiten eingebettet; eine fest eingetragene Nummer
zu wechseln hiesse Commit, Deploy und ein Einbaucode, den niemand nachzieht.
Sie steht deshalb neben Datenschutz-Link und Ueberschrift.

**Geprueft wird die Nummer, nicht nur ihre Anwesenheit.** Eine Pixel-ID ist
eine Ziffernfolge. Wer versehentlich das ganze Skript-Schnipsel aus dem Meta
Events Manager in das Feld kopiert, bekaeme sonst ein Widget, das
`<script>...` als Nummer an Facebook reicht — und merkt es nie, weil ein
Pixel, der nicht feuert, nichts meldet.
"""
import pytest

from services import pixel


class TestPixelIdPruefung:
    """`pixel.geprueft` — was als Pixel-ID durchgeht."""

    def test_eine_gewoehnliche_id_geht_durch(self):
        assert pixel.geprueft("1234567890123456") == "1234567890123456"

    def test_leer_heisst_abgeschaltet(self):
        # Der ausdrueckliche Weg, den Pixel wieder loszuwerden: Feld leeren.
        assert pixel.geprueft("") == ""
        assert pixel.geprueft(None) == ""
        assert pixel.geprueft("   ") == ""

    def test_leerzeichen_ringsum_stoeren_nicht(self):
        assert pixel.geprueft("  1234567890123456 ") == "1234567890123456"

    def test_ein_eingefuegtes_skript_wird_abgewiesen(self):
        # Der wahrscheinlichste Fehlgriff: Statt der Nummer landet der ganze
        # Schnipsel aus dem Events Manager im Feld.
        with pytest.raises(ValueError):
            pixel.geprueft("<script>fbq('init', '1234567890123456');</script>")

    def test_buchstaben_werden_abgewiesen(self):
        with pytest.raises(ValueError):
            pixel.geprueft("pixel-1234567890")

    def test_zu_kurz_wird_abgewiesen(self):
        with pytest.raises(ValueError):
            pixel.geprueft("12345")

    def test_zu_lang_wird_abgewiesen(self):
        with pytest.raises(ValueError):
            pixel.geprueft("1" * 25)

    def test_die_meldung_nennt_das_erwartete(self):
        # Eine Fehlermeldung, die nur „ungueltig" sagt, laesst den Nutzer
        # raten, was sie erwartet haette.
        with pytest.raises(ValueError, match="Ziffern"):
            pixel.geprueft("abc")
