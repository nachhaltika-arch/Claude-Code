# -*- coding: utf-8 -*-
'''Kann das Audit messen, was die Garantie zusagt? (K1 / L-165)

**Der Anlass.** Der Angebotsbaukasten sagt unter G1 „mindestens 85 von 100
Punkten bei Abnahme" zu. Der Produktivbericht vom 04.09.2026 meldet **78 %
der Kriterien geprüft** — elf tragen „nicht erhoben", Quelle jeweils
PageSpeed Insights.

**Am 05.09.2026 an Googles Schnittstelle nachgemessen:** Ein Abruf ohne
Schlüssel antwortet mit `429 RESOURCE_EXHAUSTED`. Ohne Schlüssel ist
PageSpeed damit nicht kleiner, sondern gar nicht verfügbar — und 20 von 103
Punkten fallen aus.

Die Auskunft in `/health` beantwortet die Frage „ist unsere Zusage heute
überhaupt messbar?" ohne Anmeldung. Genau daran ist sie am 04.09.
gescheitert: `/api/diagnostics/config` kennt den Schlüssel, verlangt aber
einen Zugang, den in dem Moment niemand zur Hand hatte.
'''
import pytest

from routers.betriebszustand import _erhebungszustand


@pytest.fixture()
def ohne_schluessel(monkeypatch):
    for name in ("GOOGLE_PAGESPEED_API_KEY", "PAGESPEED_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_ohne_schluessel_ist_die_garantie_nicht_messbar(ohne_schluessel):
    """Die Aussage, auf die es ankommt — sie fasst den ganzen Block zusammen."""
    stand = _erhebungszustand()

    assert stand["garantie_messbar"] is False
    assert stand["pagespeed"]["schluessel_gesetzt"] is False


@pytest.mark.parametrize("variable", ["GOOGLE_PAGESPEED_API_KEY", "PAGESPEED_API_KEY"])
def test_beide_schreibweisen_gelten(ohne_schluessel, monkeypatch, variable):
    """**Der Name allein hat schon einmal gereicht**, damit PageSpeed in
    beiden Umgebungen nie Daten lieferte (L-98): In Render hiess die Variable
    `PAGESPEED_API_KEY`, im Code `GOOGLE_PAGESPEED_API_KEY`."""
    monkeypatch.setenv(variable, "AIza" + "x" * 20)

    stand = _erhebungszustand()

    assert stand["garantie_messbar"] is True
    assert stand["pagespeed"]["variable"] == variable


def test_die_auskunft_nennt_welche_variable_gesetzt_ist(ohne_schluessel, monkeypatch):
    """Wer liest, dass etwas fehlt, muss wissen, welche Zeile gemeint ist —
    sonst trägt er den Wert in die nächstbeste ein."""
    monkeypatch.setenv("PAGESPEED_API_KEY", "AIza" + "y" * 20)

    stand = _erhebungszustand()

    assert stand["pagespeed"]["variable"] == "PAGESPEED_API_KEY"
    assert set(stand["pagespeed"]["moegliche_variablen"]) == {
        "GOOGLE_PAGESPEED_API_KEY", "PAGESPEED_API_KEY"}


def test_der_schluessel_steht_nie_in_der_auskunft(ohne_schluessel, monkeypatch):
    """**Die wichtigste Zusicherung.** `/health` ist offen; eine Auskunft über
    einen Schlüssel, die den Schlüssel mitliefert, ist schlimmer als keine.

    Dieselbe Regel wie bei den Zahlungswerten: Länge ja, Wert nie. Und der
    Schlüssel stand hier schon einmal an der falschen Stelle — bis zum
    24.08.2026 hing er als `key=` in der Abfrage-URL und damit im
    Render-Protokoll (L-98).
    """
    geheim = "AIza" + "DiesesDarfNirgendsAuftauchen"
    monkeypatch.setenv("PAGESPEED_API_KEY", geheim)

    text = repr(_erhebungszustand())

    assert geheim not in text
    assert "DiesesDarfNirgends" not in text
    # Auch kein Anfangsstueck: `AIza` ist oeffentlich bekannt, alles danach nicht.
    assert "AIzaD" not in text


def test_die_laenge_unterscheidet_leer_von_abgeschnitten(ohne_schluessel, monkeypatch):
    """Sie ist der Grund, warum überhaupt eine Zahl gemeldet wird: Ein
    abgeschnittenes Einfügen sieht sonst aus wie ein gesetzter Wert."""
    monkeypatch.setenv("PAGESPEED_API_KEY", "AIza" + "z" * 35)

    assert _erhebungszustand()["pagespeed"]["laenge"] == 39


def test_der_block_sagt_was_ohne_schluessel_passiert(ohne_schluessel):
    """Ohne diesen Satz liest jemand „nicht gesetzt" und hält es für eine
    Kleinigkeit. Es sind 20 von 103 Punkten."""
    stand = _erhebungszustand()

    assert "429" in stand["pagespeed"]["ohne_schluessel"]
    assert "20 von 103" in stand["pagespeed"]["wofuer"]
