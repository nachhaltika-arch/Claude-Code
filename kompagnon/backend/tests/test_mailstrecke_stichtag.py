"""Wer bekommt eine automatische Mailstrecke — und ab wann? (L-62)

**Der Zustand bis zum 24.08.2026.** `AUTO_SEQUENCE_SOURCES` war eine
handgepflegte Liste in `routers/leads.py`. Fünf ihrer acht Werte wurden
nirgends geschrieben; `postkarte` stand in beiden Listen und griff trotzdem
nicht, weil die Webhooks über rohes SQL an `create_lead` vorbeilaufen. Von
fünf Lead-Wegen bekam **kein einziger** die Strecke, und niemand merkte es —
das Ausbleiben einer Mail protokolliert nichts.

**Die Entscheidung vom 24.08.2026 (David).** Die Strecke wird scharf
geschaltet, aber **nur für Betriebe, die danach entstehen**. Der Bestand
bekommt nichts. Grund: Die Listen anzugleichen hätte ab dem nächsten Deploy
Post an Altdaten geschickt, darunter Kaltakquise — das berührt die
Rechtsgrundlage aus L-59.

**Zwei Bedingungen, und beide müssen erfüllt sein:**

1. **Herkunft `eingehend`** — die Person hat sich selbst gemeldet. Abgelesen
   an `services/lead_quellen.QUELLEN`, nicht an einer zweiten Liste; genau
   deren Doppelführung war der Fehler. Kaltakquise (`domain_import`,
   `csv_import`) bekommt **nie** eine automatische Strecke.
2. **Angelegt am oder nach dem Stichtag** — `STRECKE_AB`.

Eine unbekannte Quelle (Freitext wie `HWK-Koblenz` oder ein Kampagnenname)
bekommt nichts. Das ist Absicht: Wer nicht im geführten Wortschatz steht,
über den wissen wir die Herkunft nicht — und Raten wäre hier eine
Rechtsbehauptung über fremde Daten.
"""
from datetime import datetime, timedelta

import pytest

from services.lead_quellen import (
    STRECKE_AB,
    strecke_erlaubt,
    soll_strecke_starten,
)


class TestWelcheQuelleUeberhaupt:
    @pytest.mark.parametrize("quelle", [
        "embed_audit", "landing_audit", "facebook", "linkedin", "google",
        "postkarte", "telefon", "trackdesk", "stripe_checkout",
    ])
    def test_eingehende_quellen_duerfen(self, quelle):
        assert strecke_erlaubt(quelle) is True

    @pytest.mark.parametrize("quelle", ["domain_import", "csv_import"])
    def test_kaltakquise_darf_nie(self, quelle):
        assert strecke_erlaubt(quelle) is False, (
            "Kaltakquise bekommt keine automatische Strecke — das ist die "
            "Rechtsfrage aus L-59, nicht eine Einstellung."
        )

    @pytest.mark.parametrize("quelle", [
        "HWK-Koblenz", "Fruehjahrskampagne 2026", "", None, "manual",
    ])
    def test_ungefuehrte_und_haendische_quellen_bekommen_nichts(self, quelle):
        """Freitext heisst: Wir kennen die Herkunft nicht. Raten waere schlimmer."""
        assert strecke_erlaubt(quelle) is False


class TestDerStichtag:
    @staticmethod
    def _lead(quelle: str, angelegt: datetime):
        return type("Lead", (), {
            "lead_source": quelle, "created_at": angelegt,
            "email": "kunde@beispiel.de",
        })()

    def test_ein_betrieb_von_vor_dem_stichtag_bekommt_nichts(self):
        # Arrange — genau der Bestand, der nicht angeschrieben werden soll
        lead = self._lead("facebook", STRECKE_AB - timedelta(seconds=1))

        # Act & Assert
        assert soll_strecke_starten(lead) is False

    def test_ein_betrieb_ab_dem_stichtag_bekommt_die_strecke(self):
        # Arrange
        lead = self._lead("facebook", STRECKE_AB)

        # Act & Assert
        assert soll_strecke_starten(lead) is True

    def test_ohne_adresse_geht_nichts_hinaus(self):
        # Arrange
        lead = self._lead("facebook", STRECKE_AB + timedelta(days=1))
        lead.email = ""

        # Act & Assert
        assert soll_strecke_starten(lead) is False

    def test_kaltakquise_auch_nach_dem_stichtag_nicht(self):
        # Arrange — der Stichtag hebt die Herkunftsregel nicht auf
        lead = self._lead("csv_import", STRECKE_AB + timedelta(days=30))

        # Act & Assert
        assert soll_strecke_starten(lead) is False

    def test_ohne_anlegedatum_wird_nicht_geraten(self):
        """Ein Lead ohne `created_at` ist ein Altbestand — im Zweifel nichts."""
        # Arrange
        lead = self._lead("facebook", None)

        # Act & Assert
        assert soll_strecke_starten(lead) is False


class TestDieListeWirdNichtMehrDoppeltGefuehrt:
    def test_es_gibt_keine_zweite_quellenliste_mehr(self):
        """Genau die Doppelfuehrung war der Fehler (L-62)."""
        import pathlib

        quelle = (pathlib.Path(__file__).resolve().parent.parent
                  / "routers" / "leads.py").read_text(encoding="utf-8")
        assert "AUTO_SEQUENCE_SOURCES" not in quelle, (
            "In routers/leads.py steht wieder eine eigene Quellenliste. "
            "Gefuehrt wird der Wortschatz in services/lead_quellen.py — "
            "zwei Listen driften auseinander, und genau das war L-62."
        )
