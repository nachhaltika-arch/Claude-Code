# -*- coding: utf-8 -*-
"""
Was der Abonnent von seiner Messung sieht — und was er nicht sieht.

**Zwei Regeln, beide aus Vorfällen dieses Projekts:**

1. **Der interne Grund gehört nicht zum Kunden.** Er lautet
   „PERPLEXITY_API_KEY nicht gesetzt" — richtig für den Innendienst, falsch
   für den Kunden: Er nennt eine Umgebungsvariable, verrät die
   Betriebsausstattung und beantwortet seine Frage nicht. `/info` hat am
   15.08.2026 schon einmal Zugangsdaten preisgegeben.
2. **Ohne Abo keine Leistung.** Der Verlauf **ist** das Produkt; ihn vor dem
   Kauf zu zeigen hieße, ihn zu verschenken.
"""
import pathlib

import pytest

from routers.geo_payments import NICHT_ABGEFRAGT, _nennung_fuer_kunden

KARTE = (pathlib.Path(__file__).resolve().parents[3] / "kompagnon" / "frontend"
         / "src" / "components" / "GeoAddonCard.jsx")


class _Analyse:
    """Ein Stellvertreter — der Helfer liest nur Felder."""

    def __init__(self, status="active", befund=None, am=None, verlauf=None):
        self.subscription_status = status
        self.ki_sichtbarkeit = befund
        self.ki_sichtbarkeit_am = am
        self.ki_sichtbarkeit_verlauf = verlauf


BEFUND = {"anbieter": {
    "chatgpt": {"collected": True, "anzeige": "ChatGPT", "genannt_bei": 2,
                "beantwortet": 3, "von": 3},
    "perplexity": {"collected": False, "anzeige": "Perplexity",
                   "grund": "PERPLEXITY_API_KEY nicht gesetzt"},
}}


@pytest.mark.parametrize("status", ["active", "trialing"])
def test_abonnenten_sehen_ihre_messung(status):
    daten = _nennung_fuer_kunden(_Analyse(status=status, befund=BEFUND))

    assert daten is not None
    chatgpt = next(s for s in daten["systeme"] if s["schluessel"] == "chatgpt")
    assert chatgpt["genannt_bei"] == 2 and chatgpt["von"] == 3


@pytest.mark.parametrize("status", [None, "canceled", "past_due"])
def test_ohne_laufendes_abo_gibt_es_nichts(status):
    assert _nennung_fuer_kunden(_Analyse(status=status, befund=BEFUND)) is None


def test_der_schluesselname_erreicht_den_kunden_nicht():
    daten = _nennung_fuer_kunden(_Analyse(befund=BEFUND))

    perplexity = next(s for s in daten["systeme"] if s["schluessel"] == "perplexity")
    assert perplexity["genannt_bei"] is None, "ein nicht gefragtes System hat keine Zahl"
    assert perplexity["hinweis"] == NICHT_ABGEFRAGT
    assert "API_KEY" not in str(daten), "der Schlüsselname steht in der Kundenauskunft"


def test_nie_gemessen_ist_keine_null():
    """„Noch nicht gemessen" und „nirgends genannt" sind zwei Nachrichten."""
    daten = _nennung_fuer_kunden(_Analyse(befund=None, am=None))

    assert daten["gemessen_am"] is None
    assert daten["systeme"] == []

    quelle = KARTE.read_text(encoding="utf-8")
    assert "erste Messung steht noch aus" in quelle, (
        "die Karte zeigt fuer den Fall 'nie gemessen' keine eigene Auskunft")


def test_die_karte_verspricht_keinen_bericht_der_nicht_kommt():
    """Der Monatsbericht kennt die Nennung nicht — also wird keiner zugesagt.

    Bis zum 25.08.2026 stand dort, der naechste Report komme automatisch per
    E-Mail. Es gibt keinen solchen Versand.
    """
    quelle = KARTE.read_text(encoding="utf-8")

    assert "monatlich auf KI-Sichtbarkeit" not in quelle
    assert "wöchentlich" in quelle, "der Lauf ist wöchentlich, nicht monatlich"
    # **Seit dem 25.08.2026 darf die Karte den Bericht wieder zusagen** — es
    # gibt ihn jetzt (`automations/bericht_ki_nennung.py`), und er haengt am
    # Wochenlauf. Die Regel bleibt dieselbe, nur andersherum: Was zugesagt
    # wird, muss gebaut sein.
    assert "montags per E-Mail" in quelle
    from automations import bericht_ki_nennung
    assert hasattr(bericht_ki_nennung, "sende_bericht")


def test_die_karte_garantiert_keine_nennung():
    """Niemand kann eine Nennung zusichern — das steht schon in GEO-01."""
    quelle = KARTE.read_text(encoding="utf-8")
    assert "garantieren es nicht" in quelle
