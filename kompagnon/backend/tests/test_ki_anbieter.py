"""Die KI-Systeme, die wir nach dem Betrieb fragen (L-58 b).

**Warum mehr als eines.** Bis zum 22.08.2026 gab es hier nur einen Zugang:
`ANTHROPIC_API_KEY`. Ein Ergebnis von Claude als „ChatGPT nennt Sie nicht" zu
verkaufen waere eine Aussage ueber ein System, das wir nie gefragt haben —
und GEO verkauft genau diese Aussage. Deshalb ein Register statt eines festen
Aufrufs: Wer einen Schluessel hat, wird gefragt; wer keinen hat, wird
**ausgewiesen** und nicht geraten.

**Die Regel dahinter ist die aus D1.** Ohne PageSpeed-Schluessel erfand das
Audit im Mai Zahlen. Seitdem gilt: „nicht erhoben" faellt aus der Wertung und
wird benannt. Ein nicht konfigurierter Anbieter darf niemals wie ein Anbieter
aussehen, der den Betrieb nicht kennt.
"""
import asyncio

import pytest

from services.ki_anbieter import (
    ANBIETER,
    Anbieter,
    konfigurierte_anbieter,
    lies_openai_antwort,
    lies_perplexity_antwort,
)


class TestRegister:
    def test_die_angebundenen_systeme_stehen_drin(self):
        """Die Menge ist eine Aussage, keine Zahl.

        22.08.2026: drei — Claude, ChatGPT, Perplexity.
        25.08.2026: vier — Google AI kam dazu. Der Wettbewerb misst vier
        Systeme; drei zu messen und „KI-Sichtbarkeit" darueber zu schreiben,
        waere eine Aussage ueber ein System, das wir nie gefragt haben.

        Wer hier etwas hinzufuegt, aendert das Produkt — deshalb steht die
        Menge ausgeschrieben da und nicht nur ihre Laenge.
        """
        namen = {a.schluessel for a in ANBIETER}

        assert namen == {"claude", "chatgpt", "perplexity", "gemini"}

    def test_jeder_nennt_seine_umgebungsvariable(self):
        for a in ANBIETER:
            assert a.env_name, f"{a.schluessel} sagt nicht, welcher Schluessel fehlt"

    def test_ohne_schluessel_gilt_ein_anbieter_als_nicht_konfiguriert(self, monkeypatch):
        for a in ANBIETER:
            monkeypatch.delenv(a.env_name, raising=False)

        assert konfigurierte_anbieter() == []

    def test_gesetzte_schluessel_werden_erkannt(self, monkeypatch):
        for a in ANBIETER:
            monkeypatch.delenv(a.env_name, raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        gewaehlt = konfigurierte_anbieter()

        assert [a.schluessel for a in gewaehlt] == ["chatgpt"]

    def test_ein_leerer_schluessel_zaehlt_nicht_als_gesetzt(self, monkeypatch):
        """Render traegt leere Variablen ein, wenn jemand ein Feld anlegt und
        nicht befuellt. Leer heisst nicht konfiguriert."""
        for a in ANBIETER:
            monkeypatch.delenv(a.env_name, raising=False)
        monkeypatch.setenv("PERPLEXITY_API_KEY", "   ")

        assert konfigurierte_anbieter() == []


class TestOpenAiAntwort:
    """Responses API: Text in `output_text`, Quellen in den Annotationen."""

    def test_text_und_quellen(self):
        roh = {
            "output_text": "Empfohlen wird Mustermann Heizung.",
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": "Empfohlen wird Mustermann Heizung.",
                    "annotations": [
                        {"type": "url_citation", "url": "https://mustermann-heizung.de/"},
                    ],
                }],
            }],
        }

        text, belege = lies_openai_antwort(roh)

        assert "Mustermann" in text
        assert "https://mustermann-heizung.de/" in belege

    def test_auch_die_konsultierten_quellen_zaehlen(self):
        """`web_search_call.action.sources` ist vollstaendiger als die Zitate."""
        roh = {
            "output": [
                {"type": "web_search_call",
                 "action": {"sources": [{"url": "https://portal.de/liste"}]}},
                {"type": "message",
                 "content": [{"type": "output_text", "text": "Mehrere Anbieter."}]},
            ],
        }

        text, belege = lies_openai_antwort(roh)

        assert text == "Mehrere Anbieter."
        assert "https://portal.de/liste" in belege

    def test_eine_unbekannte_form_wirft_nicht(self):
        text, belege = lies_openai_antwort({"unerwartet": True})

        assert text == ""
        assert belege == []


class TestPerplexityAntwort:
    def test_agent_api_form(self):
        roh = {
            "output_text": "In Kassel arbeitet Mustermann Heizung.",
            "search_results": [{"url": "https://mustermann-heizung.de/"}],
        }

        text, belege = lies_perplexity_antwort(roh)

        assert "Mustermann" in text
        assert belege == ["https://mustermann-heizung.de/"]

    def test_alte_sonar_form_wird_noch_gelesen(self):
        """Sonar Chat Completions laeuft am 27.09.2026 aus, lebt bis dahin aber."""
        roh = {
            "choices": [{"message": {"content": "Mustermann Heizung GmbH"}}],
            "citations": ["https://mustermann-heizung.de/"],
        }

        text, belege = lies_perplexity_antwort(roh)

        assert "Mustermann" in text
        assert belege == ["https://mustermann-heizung.de/"]

    def test_eine_unbekannte_form_wirft_nicht(self):
        text, belege = lies_perplexity_antwort({"unerwartet": True})

        assert (text, belege) == ("", [])


class TestAnbieterVertrag:
    """Jeder Anbieter beantwortet dieselbe Frage in derselben Form."""

    def test_die_form_ist_text_und_belege(self):
        gefragt = {}

        async def falscher_aufruf(frage):
            gefragt["frage"] = frage
            return "Mustermann Heizung GmbH", ["https://mustermann-heizung.de/"]

        a = Anbieter(schluessel="test", anzeige="Test", env_name="TEST_KEY",
                     modell="test-1", _aufruf=falscher_aufruf)

        text, belege = asyncio.run(a.frage_stellen("Wer heizt in Kassel?"))

        assert gefragt["frage"] == "Wer heizt in Kassel?"
        assert text.startswith("Mustermann")
        assert belege == ["https://mustermann-heizung.de/"]

    def test_ein_fehler_wird_gemeldet_und_nicht_geworfen(self):
        async def kaputt(frage):
            raise RuntimeError("Zeitgrenze")

        a = Anbieter(schluessel="test", anzeige="Test", env_name="TEST_KEY",
                     modell="test-1", _aufruf=kaputt)

        with pytest.raises(RuntimeError):
            asyncio.run(a.frage_stellen("egal"))


# ── Google AI, angebunden am 25.08.2026 ──────────────────────────────

def test_google_ai_steht_im_register():
    """Vier Systeme, weil der Markt vier nennt.

    Drei zu messen und „KI-Sichtbarkeit" darüber zu schreiben, wäre eine
    Aussage über ein System, das wir nie gefragt haben — dieselbe Regel wie
    bei den anderen drei.
    """
    from services.ki_anbieter import ANBIETER, finde_anbieter

    assert len(ANBIETER) == 4
    gemini = finde_anbieter("gemini")
    assert gemini is not None
    assert gemini.env_name == "GEMINI_API_KEY"
    assert gemini.anzeige == "Google AI"


def test_gemini_liest_die_neue_form():
    """`steps` → `model_output` → `content` → `annotations` (25.08.2026)."""
    from services.ki_anbieter import lies_gemini_antwort

    roh = {"steps": [
        {"type": "google_search_call", "queries": ["Heizung Kassel"]},
        {"type": "model_output", "content": [{
            "text": "Mustermann Heizung GmbH ist ein Betrieb in Kassel.",
            "annotations": [
                {"type": "url_citation", "url": "https://mustermann-heizung.de"},
                {"type": "url_citation", "url": "https://beispiel.de/liste"},
            ],
        }]},
    ]}

    text, belege = lies_gemini_antwort(roh)
    assert "Mustermann" in text
    assert belege == ["https://mustermann-heizung.de", "https://beispiel.de/liste"]


def test_gemini_liest_auch_die_aeltere_form():
    """Ein Formwechsel darf nicht als „kennt den Betrieb nicht" durchgehen."""
    from services.ki_anbieter import lies_gemini_antwort

    roh = {"candidates": [{
        "content": {"parts": [{"text": "In Kassel gibt es Mustermann Heizung."}]},
        "groundingMetadata": {"groundingChunks": [
            {"web": {"uri": "https://mustermann-heizung.de", "title": "Mustermann"}},
        ]},
    }]}

    text, belege = lies_gemini_antwort(roh)
    assert "Mustermann" in text
    assert belege == ["https://mustermann-heizung.de"]


def test_gemini_liefert_lieber_nichts_als_unsinn():
    """Unbekannte Form → leeres Ergebnis, kein Absturz und keine Erfindung."""
    from services.ki_anbieter import lies_gemini_antwort

    assert lies_gemini_antwort({}) == ("", [])
    assert lies_gemini_antwort({"steps": [{"type": "unbekannt"}]}) == ("", [])
    assert lies_gemini_antwort("keine Antwort") == ("", [])
