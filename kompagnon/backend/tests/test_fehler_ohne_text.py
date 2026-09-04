"""Ein Fehler muss sagen, welcher er war — auch wenn er selbst schweigt.

**Der Befund (31.08.2026, L-58).** Beim ersten echten Lauf gegen Perplexity
stand im Bericht:

    ✗ Fehler:

Nichts dahinter. `str(httpx.ReadTimeout())` ist die **leere** Zeichenkette,
und `_eine_frage` gab genau dieses `str(fehler)` weiter. Ein Befund ohne
Inhalt ist schlimmer als keiner: Er sieht aus wie einer, und niemand kann ihm
nachgehen.

**Warum ausgerechnet hier.** Perplexitys Agent API fuehrt mehrere Suchen
hintereinander aus und brauchte gemessene 16,8 s, 14,6 s und 23,7 s. Eine
Zeitueberschreitung ist damit der wahrscheinlichste Fehlerfall — und
ausgerechnet der stumme.
"""
import httpx
import pytest

from services.ki_anbieter import ZEITGRENZE
from services.ki_sichtbarkeit import _eine_frage, _fehlertext


class StummerFehler(Exception):
    """Wie `httpx.ReadTimeout`: eine Ausnahme, deren `str()` leer ist."""


def test_httpx_zeitueberschreitung_ist_wirklich_stumm():
    """Die Grundlage dieses Tests, gemessen statt geglaubt.

    Faellt sie weg — weil httpx die Meldung nachruestet —, ist der Rest hier
    nicht falsch, aber der Anlass waere ein anderer. Dann soll das auffallen.
    """
    assert str(httpx.ReadTimeout("")) == ""


def test_ein_stummer_fehler_nennt_wenigstens_seine_art():
    assert _fehlertext(StummerFehler()) == "StummerFehler"
    assert _fehlertext(httpx.ReadTimeout("")) == "ReadTimeout"


def test_ein_redseliger_fehler_behaelt_seinen_text():
    """Die positive Gegenprobe.

    Ohne sie waere der Test darueber auch dann gruen, wenn `_fehlertext`
    **jeden** Text wegwuerfe — und dann waeren alle Meldungen gleich
    nichtssagend.
    """
    text = _fehlertext(ValueError("Rumpf ist kein JSON"))

    assert text.startswith("ValueError")
    assert "Rumpf ist kein JSON" in text


def test_sehr_lange_meldungen_werden_gekuerzt():
    assert len(_fehlertext(ValueError("x" * 500))) <= 200


@pytest.mark.anyio
async def test_der_bericht_bekommt_die_art_und_nicht_nichts():
    """Am Weg gemessen, nicht nur an der Hilfsfunktion.

    `_eine_frage` faengt jede Ausnahme; wenn dort weiter `str(fehler)` stuende,
    waere die Reparatur oben gebaut und nicht angeschlossen — die Klasse, die
    diesen Bestand am haeufigsten getroffen hat.
    """
    class Anbieter:
        schluessel = "PERPLEXITY_API_KEY"

        async def frage_stellen(self, frage):
            raise httpx.ReadTimeout("")

    ergebnis = await _eine_frage(Anbieter(), "Wer?", "beispiel.de", "Beispiel")

    assert ergebnis["fehler"] == "ReadTimeout"
    assert ergebnis["genannt"] is None


def test_die_zeitgrenze_haelt_abstand_zur_gemessenen_dauer():
    """Zwischen Normalfall und Grenze muss Spielraum liegen.

    Drei echte Laeufe gegen Perplexity am 31.08.2026: 16,8 s, 14,6 s und
    23,7 s. Bei 45 s schlug die Grenze im Sammellauf trotzdem zu, weil vier
    Anbieter gleichzeitig laufen. Dieselbe Lehre wie bei `PSI_TIMEOUT`: Ein
    Abbruch sieht im Ergebnis aus wie „nicht erhoben" und nicht wie „zu frueh
    abgebrochen".

    Der Test bindet die Zahl an ihre Begruendung — wer sie senkt, muss diesen
    Text lesen.
    """
    LAENGSTER_GEMESSENER_LAUF = 23.7

    assert ZEITGRENZE >= LAENGSTER_GEMESSENER_LAUF * 3
