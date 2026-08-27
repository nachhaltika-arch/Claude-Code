"""Der auslaufende Sonar-Zweig hat ein Datum — und das soll sich melden (L-81).

Perplexity hat am 22.08.2026 in der Herstellerdoku angekuendigt:
„Sonar Chat Completions is now Agent API. Sonar will be supported until
September 27, 2026."

Angebunden ist bereits die **Agent API** (`POST /v1/agent`), die Abschaltung
trifft uns also nicht. `lies_perplexity_antwort` liest die alte Form aber
**zusaetzlich** — ueber `roh["choices"][…]["message"]["content"] `—, weil ein
heute angelegter Schluessel auf beides zeigen kann.

**Nach dem 27.09.2026 ist dieser Zweig tot.** Wer ihn stehen laesst, haelt
eine Form offen, die es nicht mehr gibt, und der naechste Leser haelt sie fuer
gebraucht.

Der Befund nannte es „ein Termin, keine Baustelle". Genau das ist das
Problem an Terminen: Sie fallen niemandem auf. Dieser Test laeuft gruen, bis
das Datum erreicht ist, und wird danach rot — mit der Arbeitsanweisung im
Text, nicht mit einem Raetsel.
"""
import datetime

import pytest

from services.ki_anbieter import lies_perplexity_antwort

#: Der Tag, an dem Perplexity die alte Form abschaltet.
SONAR_ENDET_AM = datetime.date(2026, 9, 27)

ANWEISUNG = (
    "Der Sonar-Zweig in services/ki_anbieter.py::lies_perplexity_antwort ist "
    f"seit dem {SONAR_ENDET_AM:%d.%m.%Y} tot (L-81). Zu tun: den "
    "`choices`-Zweig entfernen, diesen Test loeschen und L-81 in der "
    "Soll-Ist-Analyse schliessen. Das ist kein Fehler im Code — es ist der "
    "Termin, der sich meldet."
)


def test_die_neue_form_wird_gelesen():
    """Agent API: `output_text` — das ist der Weg, der bleibt."""
    # Arrange
    roh = {"output_text": "  Zwei Betriebe genannt.  ",
           "search_results": [{"url": "https://beispiel.de"}]}

    # Act
    text, belege = lies_perplexity_antwort(roh)

    # Assert
    assert text == "Zwei Betriebe genannt."
    assert belege == ["https://beispiel.de"]


def test_die_alte_form_wird_noch_gelesen_und_hat_ein_ablaufdatum():
    """Sonar: `choices[…].message.content` — nur bis zum Stichtag."""
    # Arrange
    roh = {"choices": [{"message": {"content": "Aus der alten Form."}}],
           "citations": ["https://alt.example"]}

    # Act
    text, belege = lies_perplexity_antwort(roh)

    # Assert — solange der Zweig da ist, muss er auch funktionieren
    assert text == "Aus der alten Form."
    assert belege == ["https://alt.example"]

    if datetime.date.today() >= SONAR_ENDET_AM:
        pytest.fail(ANWEISUNG)


def test_unbekannte_form_bleibt_leer_statt_zu_scheitern():
    """Tolerant gebaut: lieber leer als ein Ausfall der ganzen Messung."""
    # Act & Assert
    assert lies_perplexity_antwort({"unerwartet": True}) == ("", [])
    assert lies_perplexity_antwort(None) == ("", [])
