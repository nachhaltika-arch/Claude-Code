# -*- coding: utf-8 -*-
"""Wer nicht zustimmt, wird nicht an Meta gemeldet.

**Die Regel hat sich zweimal gedreht, beide Male aus demselben Grund:** Eine
Einwilligung deckt nur den Zweck, den sie nennt.

- **Bis 08.09.2026** pruefte der Serverweg nur `consent_tracking` — den
  Aufrufparameter der Traegerseite. Das Haekchen im Formular wurde nicht
  gelesen.
- **08.09. bis 09.09.** galt: Haekchen **und** kein Nein von oben. Das trug,
  weil der Haekchen-Text Meta ausdruecklich nannte und sagte, die Adresse werde
  unkenntlich gemacht uebermittelt.
- **Seit 10.09.2026** nennt der Haekchen-Text Meta nicht mehr, und der
  erweiterte Abgleich ist entfallen (Entscheidung David: der lange Satz kostete
  Abschluesse, und der Nutzen des Abgleichs liegt bei 20 bis 40 Leads im Monat
  im Rauschen). Ein Haekchen, das von Auswertungsmails spricht, kann keine
  Uebermittlung an ein Werbenetzwerk begruenden — es wird deshalb nicht mehr
  gefragt. Traegt allein das Consent-Banner der Traegerseite.

**Die Umkehrung, auf die es ankommt:** Ein fehlender Wert war vorher ein
„vielleicht" und galt als Ja. Er ist jetzt ein Nein. § 25 TDDDG verlangt ein
Ja, und das Widget laeuft eingebettet auf fremden Seiten, die kein Banner
mitbringen — dort gab es nie eine Grundlage.

**Der Preis, den man kennen muss.** Eine Einbettung, die das Signal nicht
mitgibt, misst still nicht mehr. Dagegen steht die Pruefliste im
Projektdokument `claude/Consent-Text-Audit-Widget.md` und der Befund-Test am
Ende dieser Datei.
"""
import pytest

from services import meta_conversions as mc


class TestDarfMelden:
    """`darf_melden(consent_tracking)` — ein Ja der Traegerseite, sonst nichts."""

    @pytest.mark.parametrize("ja", ["1", "true", "TRUE", " 1 "])
    def test_ein_ausdrueckliches_ja_genuegt(self, ja):
        assert mc.darf_melden(ja) is True

    @pytest.mark.parametrize("nein", ["0", "false", "FALSE", " 0 "])
    def test_ein_ausdrueckliches_nein_meldet_nicht(self, nein):
        assert mc.darf_melden(nein) is False

    def test_schweigen_ist_keine_zustimmung(self):
        # Der eigentliche Fund vom 10.09. Vorher war das ein Ja — auf jeder
        # Einbettung ohne Banner griff damit keine Bremse.
        assert mc.darf_melden("") is False
        assert mc.darf_melden(None) is False

    def test_ein_unbekannter_wert_ist_kein_ja(self):
        # „vielleicht" traegt keine Einwilligung. Anders als vorher: Dort war
        # alles ausser „0"/„false" gruen, ein Tippfehler in der Einbettung
        # meldete also weiter.
        assert mc.darf_melden("ja") is False
        assert mc.darf_melden("xyz") is False


class TestKeineAdresseAnMeta:
    """Die Gegenprobe am Gegenstand: Der Serverweg kennt die Adresse nicht mehr.

    Eine Regel im Text („wird nicht uebermittelt") ist keine Zusicherung,
    solange die Adresse noch durch die Funktion laeuft, die an Meta sendet.
    """

    def test_sende_lead_nimmt_keine_email_an(self):
        import inspect
        parameter = inspect.signature(mc.sende_lead).parameters
        assert "email" not in parameter, (
            "sende_lead nimmt wieder eine E-Mail-Adresse an — dann muss der "
            "Einwilligungstext im Widget Meta erneut beim Namen nennen")

    def test_kein_hashen_mehr_im_modul(self):
        import pathlib
        quelle = pathlib.Path(mc.__file__).read_text(encoding="utf-8")
        # Die positive Haelfte zuerst: Ohne sie waere der Test auch dann
        # gruen, wenn das ganze Modul verschwunden ist.
        assert "def sende_lead" in quelle
        assert 'nutzerdaten["em"]' not in quelle, (
            "der erweiterte Abgleich ist zurueck, ohne dass der "
            "Einwilligungstext ihn nennt")


def test_der_router_benutzt_diese_regel():
    """Eine Regel, die richtig rechnet und die niemand aufruft, ist keine.

    Genau die Fehlerklasse, die dieses Projekt unter „gebaut, nicht
    angeschlossen" fuehrt.
    """
    import pathlib

    quelle = (pathlib.Path(__file__).resolve().parent.parent
              / "routers" / "widget.py").read_text(encoding="utf-8")
    assert "darf_melden(payload.consent_tracking)" in quelle, (
        "routers/widget.py entscheidet die Einwilligung selbst oder ruft "
        "darf_melden mit anderen Argumenten, statt das Banner-Votum zu fragen")
    # Die Gegenprobe zur Umkehrung: Der Formular-Haken darf hier nicht wieder
    # mitentscheiden, solange sein Text Meta nicht nennt.
    assert "darf_melden(payload.consent_tracking," not in quelle, (
        "darf_melden bekommt ein zweites Argument — wenn das der Formular-"
        "Haken ist, begruendet ein E-Mail-Text eine Meta-Uebermittlung")
    # Und die Adresse darf nicht wieder in die Funktion gehen, die sendet.
    hintergrund = quelle.split("meta_conversions.sende_lead", 1)[1][:400]
    assert "email=" not in hintergrund, (
        "die E-Mail-Adresse geht wieder an sende_lead")
