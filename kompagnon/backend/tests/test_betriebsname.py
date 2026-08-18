"""Eine Domain ist kein Firmenname, sondern ein Platzhalter.

UX-Daten. In der Betriebsliste hiess am 17.08.2026 jeder Eintrag wie seine
Domain: `alkozei.de`, `andovski.de`, `example.com`. Das sah nach fehlender
Datenpflege aus. Es war eine Zeile Code.

Der Domainimport legt den Betrieb mit `company_name=clean` an — der Domain,
als Platzhalter, bis der echte Name da ist. Der Impressum-Schritt liest ihn
kurz darauf aus und schreibt ihn:

    if data_imp.get(field) and not getattr(lead, field, None):

`company_name` ist zu diesem Zeitpunkt gefuellt — mit dem Platzhalter. Die
Bedingung ist damit falsch, und **der echte Name wird verworfen.** Dasselbe in
`enrich_lead`, das nur auf leer und „Unbekannt" prueft.

Ein Platzhalter, der sich wie ein Wert verhaelt, verhindert genau das, wofuer
er da war.
"""
import pytest

from services.betriebsname import ist_platzhalter


@pytest.mark.parametrize("name,domain", [
    ("alkozei.de", "https://alkozei.de"),
    ("ANDOVSKI.DE", "https://andovski.de"),
    ("www.dornhoefer.de", "https://dornhoefer.de"),
    ("example.com", "https://example.com"),
])
def test_die_eigene_domain_ist_ein_platzhalter(name, domain):
    assert ist_platzhalter(name, domain) is True


@pytest.mark.parametrize("name", ["", "   ", None, "Unbekannt", "unbekannt"])
def test_leer_und_unbekannt_sind_platzhalter(name):
    assert ist_platzhalter(name, "https://irgendwas.de") is True


def test_eine_fremde_domain_ist_auch_ein_platzhalter():
    """`nachhaltika.denachhaltika.de` stand so in der Liste — verrutscht,
    aber immer noch offensichtlich kein Firmenname."""
    assert ist_platzhalter("nachhaltika.denachhaltika.de", "https://nachhaltika.de") is True


@pytest.mark.parametrize("name", [
    "Müller Haustechnik GmbH",
    "Elektro Schmidt",
    "Dachdeckerei Heinen e.K.",
    "A. Vidak Sanitär",
])
def test_ein_echter_name_ist_keiner(name):
    assert ist_platzhalter(name, "https://beispiel.de") is False


def test_ein_name_mit_punkt_bleibt_ein_name():
    """„Fa. Krause" hat einen Punkt, ist aber keine Domain."""
    assert ist_platzhalter("Fa. Krause", "https://krause.de") is False


def test_ohne_domain_zaehlt_die_form_allein():
    assert ist_platzhalter("irgendwas.de", None) is True
    assert ist_platzhalter("Krause GmbH", None) is False


# ── Die Wirkung an der Stelle, an der es schiefging ────────────────────

def test_der_impressumname_ersetzt_den_platzhalter(app):
    """Der eigentliche Fehler: Der echte Name wurde verworfen."""
    from services.betriebsname import uebernehmen

    assert uebernehmen(vorhanden="alkozei.de", gefunden="Alkozei Haustechnik GmbH",
                       website_url="https://alkozei.de") == "Alkozei Haustechnik GmbH"


def test_ein_echter_name_wird_nicht_ueberschrieben(app):
    """Wer von Hand einen Namen gepflegt hat, soll ihn behalten."""
    from services.betriebsname import uebernehmen

    assert uebernehmen(vorhanden="Alkozei Haustechnik GmbH",
                       gefunden="Alkozei Haustechnik",
                       website_url="https://alkozei.de") is None


def test_ohne_fund_bleibt_alles_wie_es_ist(app):
    from services.betriebsname import uebernehmen

    assert uebernehmen(vorhanden="alkozei.de", gefunden="",
                       website_url="https://alkozei.de") is None
