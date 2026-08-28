# -*- coding: utf-8 -*-
"""Erzeugte Kundenseiten verfolgen niemanden ohne Einwilligung (L-144).

**Der Befund vom 27.08.2026.** „consent" kam im Bestand nur auf der
Mess-Seite vor, auf der Bau-Seite nirgends: Wir pruefen bei Kunden etwas, das
wir selbst nicht ausliefern.

**Was hier festgehalten wird, ist die Reihenfolge, nicht das Banner.** Der
Mangel waere ein Skript, das vor der Zustimmung feuert — nicht ein fehlender
Kasten. Deshalb liegt das Gewicht auf zwei Zusicherungen, die
gegenlaeufig sind und beide gebraucht werden:

* Ohne Tracking erscheint **nichts**. Ein Banner ohne Anlass trainiert
  Wegklicken und waere selbst ein Fehler.
* Mit Tracking erscheint der Kasten, und das Skript ist **nicht ausfuehrbar**.

Eine Zusicherung allein waere in beiden Richtungen wertlos: „nichts da" ist
auch wahr, wenn das Modul gar nichts kann, und „Kasten da" sagt nichts
darueber, ob das Skript trotzdem laeuft.
"""
import re

import pytest

from services.einwilligung import (
    MARKIERUNG, SPEICHERSCHLUESSEL, einwilligungs_block,
)
from services.netlify_service import _build_full_html

UMAMI = {
    "src": "https://analytics.example/script.js",
    "zweck": "statistik",
    "attribute": {"website-id": "abc-123"},
}


# ── Ohne Anlass kein Banner ────────────────────────────────────────────────

@pytest.mark.parametrize("ohne", [None, [], [{"zweck": "statistik"}]])
def test_ohne_tracking_entsteht_nichts(ohne):
    """Auch ein Eintrag ohne `src` ist kein Anlass — er laedt ja nichts."""
    assert einwilligungs_block(ohne) == ""


def test_das_ausgelieferte_dokument_bleibt_heute_unveraendert():
    """Heute liefert niemand Tracking mit — die Seite darf nicht anders aussehen."""
    # Arrange & Act
    dokument = _build_full_html(page_name="Start", html="<h1>Hallo</h1>",
                                company_name="Muster GmbH")

    # Assert
    assert MARKIERUNG not in dokument
    assert "einwilligung" not in dokument.lower()


# ── Mit Anlass: Kasten da, Skript gesperrt ─────────────────────────────────

def test_mit_tracking_wird_das_skript_nicht_ausfuehrbar_ausgeliefert():
    """Der Kern. `type="text/plain"` heisst: Der Browser laedt es nicht.

    Ein `<script src=…>` mit `defer` waere **kein** Ersatz — es laedt
    trotzdem, nur spaeter. Genau daran haengt der Unterschied zwischen einer
    Einwilligung und einer Beruhigung.
    """
    # Arrange & Act
    block = einwilligungs_block([UMAMI])

    # Assert
    assert 'type="text/plain"' in block
    assert f'data-src="{UMAMI["src"]}"' in block
    # Nirgends ein echtes `src`-Attribut auf einem Skript-Element:
    assert not re.search(r'<script[^>]*\ssrc=', block), (
        "ein ladbares Skript im ausgelieferten Markup — das ist der Mangel")


def test_mit_tracking_erscheint_ein_bedienbarer_kasten():
    # Arrange & Act
    block = einwilligungs_block([UMAMI])

    # Assert
    assert f'id="{MARKIERUNG}"' in block
    assert 'role="dialog"' in block
    assert f'data-{MARKIERUNG}-antwort="ja"' in block
    assert f'data-{MARKIERUNG}-antwort="nein"' in block
    assert 'aria-labelledby' in block, "ohne Beschriftung ist der Dialog unbedienbar"


def test_ablehnen_ist_genauso_erreichbar_wie_zustimmen():
    """Eine Seite, auf der nur „Ja" ein Knopf ist, fragt nicht, sie draengt."""
    # Arrange & Act
    block = einwilligungs_block([UMAMI])
    knoepfe = re.findall(r'<button[^>]*data-' + MARKIERUNG + r'-antwort="(\w+)"', block)

    # Assert
    assert sorted(knoepfe) == ["ja", "nein"]


def test_die_datenschutzerklaerung_wird_verlinkt():
    # Arrange & Act
    block = einwilligungs_block([UMAMI], datenschutz_pfad="/datenschutz")

    # Assert
    assert 'href="/datenschutz"' in block


def test_zusatzattribute_ueberleben_die_sperre():
    """Umami braucht `data-website-id` — ohne sie zaehlt es ins Leere."""
    # Arrange & Act
    block = einwilligungs_block([UMAMI])

    # Assert
    assert 'data-website-id="abc-123"' in block


def test_der_speicherschluessel_ist_versioniert():
    """Aendern sich die Zwecke, darf alte Zustimmung nicht stillschweigend gelten."""
    assert SPEICHERSCHLUESSEL.endswith("_v1")
    assert SPEICHERSCHLUESSEL in einwilligungs_block([UMAMI])


def test_widerruf_ist_vorgesehen():
    """Eine Einwilligung, die sich nicht zuruecknehmen laesst, ist keine."""
    # Arrange & Act
    block = einwilligungs_block([UMAMI])

    # Assert
    assert f"{MARKIERUNG}-widerruf" in block
    assert "removeItem" in block


# ── Der Weg durch das ganze Dokument ───────────────────────────────────────

def test_tracking_kommt_nur_durch_die_sperre_ins_dokument():
    # Arrange & Act
    dokument = _build_full_html(page_name="Start", html="<h1>Hallo</h1>",
                                company_name="Muster GmbH",
                                tracking_skripte=[UMAMI])

    # Assert
    assert MARKIERUNG in dokument
    assert 'type="text/plain"' in dokument
    skripte_mit_src = re.findall(r'<script[^>]*\ssrc=[^>]*>', dokument)
    assert skripte_mit_src == [], f"ungesperrtes Skript: {skripte_mit_src}"


def test_die_markierung_ist_kein_fremder_anbietername():
    """Kein Erschleichen des eigenen Pruefergebnisses.

    `detect_consent` fragt nicht „gibt es eine Einwilligung", sondern „steht
    einer von 19 Anbieternamen im HTML". Einen davon hier hineinzuschreiben,
    damit das eigene Werkzeug gruen wird, waere gruen und blind — genau die
    Bauart, vor der `waechter_ohne_wirkung` warnt. Dass unser Pruefer diese
    Loesung **nicht** erkennt, ist ein bekannter Befund der Messseite und dort
    zu entscheiden, nicht hier zu umgehen.
    """
    # Arrange
    from services.audit_collectors import CMP_SIGNATURES, detect_consent

    # Act
    block = einwilligungs_block([UMAMI])
    erkannt = detect_consent(block)

    # Assert
    assert MARKIERUNG not in CMP_SIGNATURES
    assert not any(name in MARKIERUNG for name in CMP_SIGNATURES)
    assert erkannt["cmp_detected"] is False, (
        "wenn das je True wird, wurde entweder der Pruefer bewusst erweitert "
        "(dann diesen Test anpassen) oder ein Anbietername eingeschmuggelt")
