# -*- coding: utf-8 -*-
"""
Der wöchentliche Nennungsbericht — was er sagt und was er verschweigt.

Die Kundenkarte hat ihn bis zum 25.08.2026 versprochen, ohne dass es ihn gab.
Diese Tests halten fest, was er darf und was nicht.
"""
from unittest.mock import patch

from automations import bericht_ki_nennung as bericht

BEFUND = {"anbieter": {
    "chatgpt": {"collected": True, "anzeige": "ChatGPT",
                "genannt_bei": 2, "beantwortet": 3},
    "perplexity": {"collected": False, "anzeige": "Perplexity",
                   "grund": "PERPLEXITY_API_KEY nicht gesetzt"},
}}
VERLAUF = [
    {"am": "2026-08-18", "anbieter": {"chatgpt": {"genannt_bei": 1}}},
    {"am": "2026-08-25", "anbieter": {"chatgpt": {"genannt_bei": 2}}},
]


def test_der_bericht_nennt_die_richtung():
    """Die Frage des Abos lautet: mehr oder weniger als beim letzten Mal?"""
    _, html, text = bericht.baue_bericht("Muster GmbH", BEFUND, VERLAUF)

    assert "2 von 3" in text
    assert "vorher 1" in text and "vorher 1" in html


def test_ohne_vorlauf_wird_nichts_verglichen():
    """Der erste Bericht behauptet keinen Anstieg aus dem Nichts."""
    _, _, text = bericht.baue_bericht("Muster GmbH", BEFUND, VERLAUF[-1:])

    assert "vorher" not in text


def test_nicht_abgefragte_systeme_werden_ausgewiesen():
    """Sonst liest der Kunde drei Systeme und hält sie für alle."""
    _, html, text = bericht.baue_bericht("Muster GmbH", BEFUND, VERLAUF)

    assert "Nicht abgefragt" in text
    assert "Perplexity" in text
    assert "0 von" not in text, "ein nicht gefragtes System bekommt keine Zahl"
    assert "API_KEY" not in html + text, "der Schlüsselname steht in der Mail"


def test_ohne_messung_geht_nichts_hinaus():
    """Eine Mail „0 von 3" für ein nie gefragtes System ist die teuerste
    Nachricht, die dieses Produkt verschicken kann."""
    leer = {"anbieter": {"chatgpt": {"collected": False, "anzeige": "ChatGPT"}}}

    assert bericht.baue_bericht("Muster", leer, []) == (None, None, None)
    assert bericht.sende_bericht("kunde@example.de", "Muster", leer, []) is False


def test_ohne_adresse_kein_versand():
    assert bericht.sende_bericht("", "Muster", BEFUND, VERLAUF) is False


def test_der_probemodus_verschickt_nicht():
    """Im Probemodus wird protokolliert, nicht zugestellt."""
    with patch.object(bericht, "probemodus", return_value=True):
        with patch("services.email.send_email") as versand:
            assert bericht.sende_bericht("kunde@example.de", "Muster",
                                         BEFUND, VERLAUF) is True
            versand.assert_not_called()


def test_der_bericht_sichert_keine_nennung_zu():
    """Niemand kann eine Nennung garantieren — auch keine Mail."""
    _, html, text = bericht.baue_bericht("Muster GmbH", BEFUND, VERLAUF)

    for fassung in (html, text):
        assert "entscheidet dessen Anbieter" in fassung
        assert "garantieren wir" not in fassung


def test_der_wochenlauf_berichtet():
    """Ein Bericht, den niemand auslöst, ist keiner."""
    import inspect

    from automations import job_ki_sichtbarkeit

    quelle = inspect.getsource(job_ki_sichtbarkeit)
    assert "sende_bericht" in quelle
    assert '"berichtet"' in quelle, "die Bilanz weist den Versand nicht aus"
