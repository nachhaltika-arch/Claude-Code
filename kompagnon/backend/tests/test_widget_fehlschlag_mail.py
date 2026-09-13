# -*- coding: utf-8 -*-
"""Die eine Mail, die einen verlorenen Lead sichtbar macht (L-184).

**Der Befund.** Schlägt die Erhebung fehl, geht **gar nichts** raus:
`_notify_widget_requester` steigt aus, solange der Status nicht `completed`
ist. Der Besucher hat seine Adresse hinterlassen, wartet — und hört nie
wieder etwas. Bei bezahltem Verkehr ist das die Stelle, an der Geld ohne
Spur verschwindet.

**Warum das kein Bruch des eigenen Wortes ist.** `lead_nachfassen` hält
fest, dass an eine unbestätigte Adresse nichts Unaufgefordertes geht — der
Satz aus `verify_email` lautet „Ohne Ihre Bestätigung schicken wir nichts
weiter und melden uns nicht von selbst". Diese Mail hier fällt nicht
darunter, und zwar aus zwei Gründen:

1. Sie ist die **Antwort auf die eigene Anfrage** des Besuchers, keine
   Erinnerung und keine Werbung.
2. Sie ist die **erste** Mail. Der Satz, den sie angeblich brechen würde,
   ist ihm nie zugegangen — `verify_email` wurde ja gerade nicht versendet.

**Was sie nicht enthält.** Keine Punktzahl, keinen Mangel, kein Angebot,
keinen Knopf zum Bericht. Es gibt keinen Bericht. Wer sie nicht angefordert
hat, erfährt aus ihr nichts über die Seite — dieselbe Regel wie bei
`verify_email`.
"""
import pytest

from services import widget_report
from services.analyse_fehler import (ADRESSE_UNBEKANNT, NICHT_ERREICHBAR,
                                     UNBEKANNT, ZEITGRENZE)

ALLE = (ADRESSE_UNBEKANNT, NICHT_ERREICHBAR, ZEITGRENZE, UNBEKANNT)


def _mail(grund, firma="Muster GmbH"):
    return widget_report.fehlschlag_email(company=firma, grund=grund)


class TestJederGrundHatEineMail:
    @pytest.mark.parametrize("grund", ALLE)
    def test_betreff_und_rumpf_sind_gefuellt(self, grund):
        betreff, html = _mail(grund)
        assert betreff.strip()
        assert len(html) > 400

    @pytest.mark.parametrize("grund", ALLE)
    def test_die_firma_steht_darin(self, grund):
        _, html = _mail(grund, "Sanitär Müller")
        assert "Sanitär Müller" in html

    def test_ein_unbekannter_schluessel_faellt_auf_unbekannt_zurueck(self):
        """Ein neuer Grund darf keine leere Mail erzeugen."""
        betreff, html = _mail("ein_grund_den_es_noch_nicht_gibt")
        _, html_unbekannt = _mail(UNBEKANNT)
        assert html == html_unbekannt


class TestKeineWerbungKeinBefund:
    """Dieselbe Zurückhaltung wie in `verify_email` — aus demselben Grund."""

    @pytest.mark.parametrize("grund", ALLE)
    def test_keine_punktzahl_und_kein_angebot(self, grund):
        _, html = _mail(grund)
        for verboten in ("/100", "Punkte", "Websprint", "Angebot", "€"):
            assert verboten not in html, f"{verboten!r} gehört nicht in diese Mail"

    @pytest.mark.parametrize("grund", ALLE)
    def test_kein_link_auf_einen_bericht(self, grund):
        _, html = _mail(grund)
        assert "/report/" not in html


class TestDerSatzGibtNichtDemBesucherDieSchuld:
    """Der Kern von L-184."""

    def test_nur_bei_unaufloesbarer_adresse_wird_das_pruefen_verlangt(self):
        _, html = _mail(ADRESSE_UNBEKANNT)
        assert "Adresse" in html

    @pytest.mark.parametrize("grund", [NICHT_ERREICHBAR, ZEITGRENZE, UNBEKANNT])
    def test_sonst_nicht(self, grund):
        """Bei ConnectTimeout läuft seine Seite — wir kommen nur nicht hin."""
        _, html = _mail(grund)
        assert "Bitte die Adresse prüfen" not in html
        assert "Bitte prüfen Sie die Adresse" not in html

    def test_bei_nicht_erreichbar_nehmen_wir_es_auf_uns(self):
        _, html = _mail(NICHT_ERREICHBAR)
        assert "von hier" in html or "wir" in html.lower()


class TestZusageNurWennSieGehaltenWird:
    """Wo wir uns melden, muss der Fall auch im Werkzeug auftauchen.

    Der Analysestand steht seit dem 10.09. in der Anfrageliste — deshalb ist
    „wir sehen es uns an" eine Zusage, die jemand einlösen kann. Bei einem
    Tippfehler in der Adresse gibt es nichts anzusehen; dort wird nichts
    versprochen, sondern um einen zweiten Versuch gebeten.
    """

    @pytest.mark.parametrize("grund", [NICHT_ERREICHBAR, ZEITGRENZE, UNBEKANNT])
    def test_wir_melden_uns(self, grund):
        _, html = _mail(grund)
        assert "melden uns" in html

    def test_bei_einem_tippfehler_wird_nichts_zugesagt(self):
        _, html = _mail(ADRESSE_UNBEKANNT)
        assert "melden uns" not in html
