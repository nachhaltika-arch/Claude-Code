# -*- coding: utf-8 -*-
"""Sender und Empfaenger des Ereignisses „Analyse gestartet" passen zusammen.

**Was diese Datei kann und was nicht.** Der eigentliche Beleg ist der
Durchlauf im Browser vom 15.09.2026: Widget sendet, Elternseite empfaengt,
`fbq.callMethod('track','InitiateCheckout')` wird gerufen, ohne Einwilligung
passiert nichts. Das laesst sich hier nicht wiederholen — der Gegenstand ist
eine HTML-Datei plus ein Einbau-Block, der auf einer **fremden** Seite lebt.

Was hier geprueft wird, ist deshalb enger und trotzdem nicht wertlos: dass
die beiden Seiten **denselben Namen** benutzen und dass die drei Zusagen im
Quelltext stehen, die man beim naechsten Umbau versehentlich herausnimmt.
Ein Waechter, der weiss, was er nicht weiss, ist besser als einer, der so
tut als sei er der Durchlauf.
"""
import pathlib

import pytest

WURZEL = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "public" / "embed"
WIDGET = WURZEL / "audit-widget.html"
README = WURZEL / "README.md"

#: Der Name der Nachricht. Er steht an genau zwei Stellen, und wenn sie
#: auseinanderlaufen, faellt nichts aus — es wird nur nichts mehr gemessen.
NACHRICHT = "kpg-analyse-gestartet"


@pytest.fixture(scope="module")
def widget():
    return WIDGET.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def block():
    """Der fertige Einbau-Block aus dem README — der, den David einsetzt."""
    teile = README.read_text(encoding="utf-8").split("```html")
    for teil in teile[1:]:
        rumpf = teil.split("```", 1)[0]
        if NACHRICHT in rumpf:
            return rumpf
    raise AssertionError(f"Kein Einbau-Block mit {NACHRICHT} im README")


def test_das_widget_meldet_den_start(widget):
    assert f"parent.postMessage({{ type: '{NACHRICHT}' }}, '*')" in widget


def test_die_meldung_traegt_nichts_ueber_den_besucher(widget):
    """Die Nachricht geht mit `'*'` an ein fremdes Fenster — alles darin ist
    fuer jeden lesbar, der dort ein Skript hat. Gebraucht wird die Tatsache,
    nicht wer es war."""
    zeile = next(z for z in widget.splitlines() if NACHRICHT in z and "postMessage" in z)
    for verboten in ("email", "url", "cleanUrl", "website"):
        assert verboten not in zeile, f"{verboten!r} hat in der Meldung nichts zu suchen"


def test_gemeldet_wird_beim_absenden_nicht_beim_tippen(widget):
    """Wer nur ins Feld klickt, hat keine Analyse begonnen. Der Aufruf steht
    als erste Zeile in `startAudit` — dort, wo der Lauf wirklich beginnt."""
    rumpf = widget.split("function startAudit(", 1)[1]
    assert rumpf.split("\n")[1].strip() == "meldeAnalyseGestartet();"


def test_genau_einmal_je_sitzung(widget):
    """Dieselbe Sperre wie beim Lead. Ohne sie zaehlt ein zweiter Anlauf als
    zweiter Start, und die Quote „Start zu Lead" sieht schlechter aus als die
    Wirklichkeit."""
    rumpf = widget.split("function meldeAnalyseGestartet()", 1)[1][:300]
    assert "if (analyseGemeldet) return;" in rumpf
    assert "analyseGemeldet = true;" in rumpf


def test_der_einbaublock_hoert_auf_dieselbe_nachricht(block):
    """**Der Fund, den nur ein Vergleich zeigt.** Laufen die beiden Namen
    auseinander, faellt nichts aus: Das Widget sendet weiter, die Seite hoert
    weiter zu, und gemessen wird nichts mehr."""
    assert f"d.type === '{NACHRICHT}'" in block


def test_der_einbaublock_prueft_die_einwilligung_vor_dem_ereignis(block):
    """Und zwar mit **derselben** Funktion, die auch vor dem Laden des Pixels
    steht. Zwei Pruefungen fuer dieselbe Frage laufen auseinander — und die
    Abweichung faellt genau dann auf, wenn jemand widersprochen hat."""
    zweig = block.split(f"d.type === '{NACHRICHT}'", 1)[1].split("fbq(", 1)[0]
    assert "einwilligung()" in zweig
    assert ".marketing" in zweig


def test_der_einbaublock_prueft_herkunft_und_absender(block):
    """Ohne beides nimmt die Seite ein `InitiateCheckout` von jedem an, der
    ihr eine Nachricht schickt."""
    assert "e.origin !== URSPRUNG" in block
    assert "f.contentWindow !== e.source" in block


def test_der_einbaublock_meldet_nur_einmal_je_seitenaufruf(block):
    zweig = block.split(f"d.type === '{NACHRICHT}'", 1)[1].split("fbq(", 1)[0]
    assert "startGemeldet" in zweig
