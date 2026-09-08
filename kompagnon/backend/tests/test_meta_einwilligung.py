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

**Was diese Datei ausdruecklich nicht behauptet.** Das Haekchen lautet „…
per E-Mail kontaktieren" und nennt Meta nicht. Es als Zustimmung zur
Messung zu lesen ist die **vorsichtigere** Auslegung, nicht die saubere; die
saubere waere ein eigener Satz im Formular. Das ist eine Textentscheidung
und gehoert David, nicht diesem Code.
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
