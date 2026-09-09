# -*- coding: utf-8 -*-
"""Wer nicht zustimmt, wird nicht an Meta gemeldet (08.09.2026).

**Der blinde Fleck.** Der Serverweg zur Conversions API pruefte nur
`consent_tracking` — den Aufrufparameter, den die **Traegerseite** mitgibt.
Das Haekchen, das der Besucher **im Formular selbst** setzt oder eben nicht,
wurde an drei Stellen ausgewertet (Double-Opt-in, Zeitpunkt, Speicherung)
und beim Meta-Weg an keiner.

Folge: Wer das Haekchen nicht setzte, weil er keine Werbepost will, bekam
seine Adresse trotzdem gehasht an Meta gemeldet. Und auf jeder Einbettung
ohne `consent`-Parameter — also ueberall ausser der neuen Landingpage —
griff gar keine Bremse.

**Die Regel jetzt: es braucht ein Ja, und es darf kein Nein geben.**
Zustimmung ist nichts, was durch Schweigen entsteht.

**Was hier stand und nicht mehr gilt (09.09.2026).** „Das Haekchen lautet
„… per E-Mail kontaktieren" und nennt Meta nicht" — das war bis zum 09.09.
richtig und ist es nicht mehr. Der Satz nennt Meta jetzt beim Namen und sagt,
dass die Adresse unkenntlich gemacht uebermittelt wird; damit deckt die
Einwilligung den Zweck, an dem `darf_melden` haengt. Entscheidung David am
09.09.2026.

**Warum die alte Zeile nicht einfach geloescht wurde.** Eine Testdatei, deren
Kopf beim Nachsehen widerlegt wird, verliert ihre Glaubwuerdigkeit auch dort,
wo sie recht hat — dieselbe Lehre wie bei der Sprachregel in `CLAUDE.md`. Der
Waechter ueber den Wortlaut steht im Frontend
(`src/utils/widgetPixel.test.js`, „Was der Besucher zustimmt"), weil der Text
dort liegt.
"""
import pytest

from services import meta_conversions as mc


class TestDarfMelden:
    """`darf_melden(consent_tracking, consent_marketing)`."""

    def test_haekchen_gesetzt_und_kein_nein_von_oben(self):
        assert mc.darf_melden("", True) is True
        assert mc.darf_melden("1", True) is True

    def test_ohne_haekchen_wird_nicht_gemeldet(self):
        # Der eigentliche Fund. Vorher war das ein Ja.
        assert mc.darf_melden("", False) is False
        assert mc.darf_melden("1", False) is False

    @pytest.mark.parametrize("nein", ["0", "false", "FALSE", " 0 "])
    def test_ein_nein_der_traegerseite_sticht_das_haekchen(self, nein):
        # Der Cookie-Banner der Seite hat Vorrang: Wer dort Marketing
        # ablehnt, hat abgelehnt — auch wenn er im Formular ein Haekchen
        # setzt, das von E-Mail spricht.
        assert mc.darf_melden(nein, True) is False

    def test_ein_unbekannter_wert_gilt_nicht_als_nein(self):
        # „vielleicht" ist kein Nein. Sonst waere jeder Tippfehler in der
        # Einbettung eine stille Abschaltung, die niemand findet.
        assert mc.darf_melden("ja", True) is True
        assert mc.darf_melden("xyz", True) is True

    def test_fehlende_angaben_werfen_nicht(self):
        assert mc.darf_melden(None, None) is False
        assert mc.darf_melden(None, True) is True


def test_der_router_benutzt_diese_regel():
    """Die Gegenprobe am Gegenstand.

    Eine Regel, die richtig rechnet und die niemand aufruft, ist keine —
    genau die Fehlerklasse, die dieses Projekt unter „gebaut, nicht
    angeschlossen" fuehrt.
    """
    import pathlib

    quelle = (pathlib.Path(__file__).resolve().parent.parent
              / "routers" / "widget.py").read_text(encoding="utf-8")
    assert "darf_melden" in quelle, (
        "routers/widget.py entscheidet die Einwilligung selbst, statt "
        "meta_conversions.darf_melden zu fragen")
