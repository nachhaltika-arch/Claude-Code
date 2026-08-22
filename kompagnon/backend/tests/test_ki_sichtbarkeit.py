"""Ob eine Maschine den Betrieb auf eine Frage hin **nennt** (L-58 b).

Der Katalog misst seit dem 21.08.2026 die **Lesbarkeit** — kein KI-Crawler
ausgesperrt, `llms.txt` vorhanden (`se_ki_lesbar`, 3 P). Das ist die
Voraussetzung, nicht das Ergebnis. Ob ein Suchender, der eine KI fragt, den
Betrieb genannt bekommt, misst dort nichts.

**Was hier gemessen wird — und was nicht.** Gefragt wird Claude mit
Websuche. Das ist **nicht** ChatGPT und nicht Perplexity; fuer die gibt es in
diesem Haus keinen Zugang, und ein Ergebnis von Claude als „ChatGPT nennt Sie
nicht" zu verkaufen waere eine Behauptung ueber ein System, das wir nie
gefragt haben. Der Befund traegt deshalb sein Modell mit sich, und der
Bericht muss es nennen.

**Warum das ein eigener Dienst ist und nicht ein Kriterium.** Jeder Lauf
kostet Geld — echte Suchanfragen an ein fremdes Modell. Ein kostenloses Audit
mit einer Kostenstelle je Aufruf ist ein anderes Produkt als eines ohne. Bis
diese Entscheidung gefallen ist, haengt hier nichts am Score.
"""
import asyncio
import threading

import pytest

from services.ki_anbieter import Anbieter
from services.ki_sichtbarkeit import (
    baue_fragen,
    ist_genannt,
    pruefe_ki_sichtbarkeit,
)


# ── Die Fragen ───────────────────────────────────────────────────────

class TestFragen:
    def test_gewerk_und_ort_stehen_in_jeder_frage(self):
        # Arrange & Act
        fragen = baue_fragen(gewerk="Heizung", ort="Kassel")

        # Assert
        assert fragen, "ohne Fragen gibt es nichts zu messen"
        for frage in fragen:
            assert "Kassel" in frage
            assert "Heizung" in frage.lower() or "heizung" in frage.lower()

    def test_ohne_ort_wird_nicht_geraten(self):
        """Ein erfundener Ort misst die Sichtbarkeit an einem falschen Markt."""
        assert baue_fragen(gewerk="Heizung", ort="") == []
        assert baue_fragen(gewerk="", ort="Kassel") == []

    def test_die_fragen_sind_verschieden(self):
        fragen = baue_fragen(gewerk="Sanitär", ort="Kassel")

        assert len(set(fragen)) == len(fragen)


# ── Die Erkennung ────────────────────────────────────────────────────

class TestErkennung:
    def test_die_eigene_adresse_zaehlt(self):
        assert ist_genannt(
            antwort="Empfehlenswert ist die Firma Mustermann.",
            belege=["https://mustermann-heizung.de/leistungen"],
            domain="mustermann-heizung.de",
            name="Mustermann Heizung GmbH",
        )

    def test_der_name_im_text_zaehlt_auch_ohne_beleg(self):
        assert ist_genannt(
            antwort="In Kassel arbeitet unter anderem Mustermann Heizung.",
            belege=["https://irgendein-portal.de/liste"],
            domain="mustermann-heizung.de",
            name="Mustermann Heizung GmbH",
        )

    def test_ein_fremder_betrieb_zaehlt_nicht(self):
        assert not ist_genannt(
            antwort="Empfehlenswert ist die Firma Schmidt & Söhne.",
            belege=["https://schmidt-soehne.de/"],
            domain="mustermann-heizung.de",
            name="Mustermann Heizung GmbH",
        )

    def test_die_rechtsform_allein_macht_keinen_treffer(self):
        """Sonst gilt jede GmbH im Text als der eigene Betrieb."""
        assert not ist_genannt(
            antwort="Mehrere Anbieter, darunter eine GmbH aus der Region.",
            belege=[],
            domain="mustermann-heizung.de",
            name="Mustermann Heizung GmbH",
        )

    def test_www_und_grossschreibung_stoeren_nicht(self):
        assert ist_genannt(
            antwort="Siehe WWW.Mustermann-Heizung.DE",
            belege=[],
            domain="www.mustermann-heizung.de",
            name="Mustermann Heizung GmbH",
        )


# ── Der Lauf ─────────────────────────────────────────────────────────


def _anbieter(schluessel, antworten):
    """Ein Anbieter, der der Reihe nach liefert — oder wirft."""
    rest = list(antworten)

    async def aufruf(frage):
        if not rest:
            return "keine Angabe", []
        naechste = rest.pop(0)
        if isinstance(naechste, Exception):
            raise naechste
        return naechste

    return Anbieter(schluessel=schluessel, anzeige=schluessel.title(),
                    env_name=f"{schluessel.upper()}_KEY", modell=f"{schluessel}-1",
                    _aufruf=aufruf)


TREFFER = ("Mustermann Heizung GmbH ist dort tätig.",
           ["https://mustermann-heizung.de/"])
DANEBEN = ("Empfohlen wird Schmidt & Söhne.", ["https://schmidt.de/"])

BETRIEB = {"name": "Mustermann Heizung GmbH", "domain": "mustermann-heizung.de",
           "gewerk": "Heizung", "ort": "Kassel"}


def _lauf(anbieter, **zusatz):
    return asyncio.run(pruefe_ki_sichtbarkeit(
        **{**BETRIEB, **zusatz}, anbieter=anbieter))


class TestLauf:
    def test_jeder_anbieter_bekommt_ein_eigenes_ergebnis(self):
        ergebnis = _lauf([
            _anbieter("chatgpt", [TREFFER, DANEBEN]),
            _anbieter("claude", [DANEBEN, DANEBEN]),
        ], max_fragen=2)

        assert ergebnis["collected"] is True
        assert ergebnis["anbieter"]["chatgpt"]["genannt_bei"] == 1
        assert ergebnis["anbieter"]["claude"]["genannt_bei"] == 0

    def test_ein_nicht_angebundener_anbieter_gilt_als_nicht_erhoben(self, monkeypatch):
        """Die Regel aus D1: nicht erhoben ist nicht dasselbe wie nicht gefunden.

        Wer ohne Perplexity-Schluessel „Perplexity: 0 von 5" druckt, sagt dem
        Betrieb, er sei dort unsichtbar — gemessen wurde nie.
        """
        from services import ki_anbieter

        for a in ki_anbieter.ANBIETER:
            monkeypatch.delenv(a.env_name, raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        ergebnis = asyncio.run(pruefe_ki_sichtbarkeit(**BETRIEB, max_fragen=1))

        offen = ergebnis["anbieter"]["perplexity"]
        assert offen["collected"] is False
        assert "PERPLEXITY_API_KEY" in offen["grund"]
        assert "genannt_bei" not in offen

    def test_ohne_jeden_zugang_wird_nichts_erhoben(self, monkeypatch):
        from services import ki_anbieter

        for a in ki_anbieter.ANBIETER:
            monkeypatch.delenv(a.env_name, raising=False)

        ergebnis = asyncio.run(pruefe_ki_sichtbarkeit(**BETRIEB))

        assert ergebnis["collected"] is False
        assert ergebnis["grund"]

    def test_ein_ausgefallener_anbieter_kippt_die_anderen_nicht(self):
        ergebnis = _lauf([
            _anbieter("chatgpt", [RuntimeError("Zeitgrenze")]),
            _anbieter("claude", [TREFFER]),
        ], max_fragen=1)

        assert ergebnis["anbieter"]["chatgpt"]["fehler"] == 1
        assert ergebnis["anbieter"]["chatgpt"]["genannt_bei"] == 0
        assert ergebnis["anbieter"]["claude"]["genannt_bei"] == 1

    def test_jeder_befund_traegt_sein_modell(self):
        """Ohne Modellangabe liest jemand ein Claude-Ergebnis als ChatGPT."""
        ergebnis = _lauf([_anbieter("claude", [TREFFER])], max_fragen=1)

        assert ergebnis["anbieter"]["claude"]["modell"] == "claude-1"

    def test_ohne_ort_wird_nichts_erhoben(self):
        ergebnis = _lauf([_anbieter("claude", [TREFFER])], ort="")

        assert ergebnis["collected"] is False

    def test_jede_frage_steht_einzeln_im_ergebnis(self):
        """Ein Gesamtwert ohne die Fragen dahinter ist nicht nachpruefbar."""
        ergebnis = _lauf([_anbieter("claude", [TREFFER])], max_fragen=1)

        fragen = ergebnis["anbieter"]["claude"]["fragen"]
        assert len(fragen) == 1
        assert fragen[0]["frage"] and fragen[0]["genannt"] is True

    def test_die_gesamtzahl_zaehlt_nur_erhobene_anbieter(self):
        ergebnis = _lauf([
            _anbieter("chatgpt", [TREFFER]),
            _anbieter("claude", [DANEBEN]),
        ], max_fragen=1)

        assert ergebnis["erhoben_bei"] == 2
        assert ergebnis["genannt_bei"] == 1
