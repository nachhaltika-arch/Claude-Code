# -*- coding: utf-8 -*-
"""Die Kaufknöpfe der Berichtsseite (Wunsch David, 10.09.2026).

**Warum Einstellungen und nicht der Entwurf.** Der Entwurf trug zwei feste
Stripe-Zahllinks im `href`. Ein Kaufweg im Quelltext ist dieselbe Falle wie
ein Preis im Quelltext (L-29): Er wandert nicht mit, wenn sich das Konto
aendert — und beim Kontowechsel auf WEBSPRINT am 08.09. hat genau das
gedroht, nur bei Preisen.

**Eine Adresse je Produkt, nicht je Ort.** Check PLUS wird an zwei Stellen
angeboten — im Teaser und im Bericht. Beide lesen `widget_check_plus_url`.
Zwei Einstellungen fuer dasselbe Produkt waeren zwei Wahrheiten, und die
zweite waere irgendwann veraltet.

**Ohne Adresse fuehrt der Knopf in den Kalender.** Nicht ins Leere und nicht
weg: Wer kaufen will und keinen Kaufweg findet, soll wenigstens einen Termin
bekommen. Das ist der Zustand von heute, und er bleibt der Rueckfall.
"""
import pytest

from services import bericht_daten


class _Db:
    def execute(self, *a, **k):
        class E:
            def mappings(self_):
                class M:
                    def first(self__): return None
                return M()
        return E()
    def rollback(self): pass


class _Audit:
    company_name = "Muster GmbH"; website_url = "https://muster.de"
    total_score = 61; item_scores = {}; item_sources = {}; item_belege = {}
    coverage = 0; blockers = "[]"; erkannte_branche = ""; branchenklasse = ""
    level = "Homepage Standard Bronze"


KAUF_RELAUNCH = "https://buy.stripe.com/aFa8wP8FR6WZdsG0no9Zm00"
KAUF_CHECK = "https://buy.stripe.com/eVq8wP9JV4ORdsGgmm9Zm01"


def _daten(**einstellungen):
    return bericht_daten.aufbauen(_Db(), _Audit(), einstellungen=einstellungen)


class TestMitAdresse:
    def test_relaunch_fuehrt_zum_kauf(self):
        d = _daten(bericht_kauf_relaunch_url=KAUF_RELAUNCH)
        assert d["kaufUrlRelaunch"] == KAUF_RELAUNCH

    def test_check_plus_nimmt_dieselbe_einstellung_wie_der_teaser(self):
        d = _daten(widget_check_plus_url=KAUF_CHECK)
        assert d["kaufUrlCheckPlus"] == KAUF_CHECK


class TestOhneAdresse:
    def test_beide_fallen_auf_den_kalender_zurueck(self):
        d = _daten(widget_booking_url="https://kalender.example/termin")
        assert d["kaufUrlRelaunch"] == d["terminUrl"]
        assert d["kaufUrlCheckPlus"] == d["terminUrl"]
        assert d["terminUrl"]

    def test_kein_knopf_zeigt_ins_leere(self):
        """Auch ohne jede Einstellung: `termin_url` liefert einen Standard."""
        d = _daten()
        assert d["kaufUrlRelaunch"]
        assert d["kaufUrlCheckPlus"]


class TestSchranke:
    @pytest.mark.parametrize("boese", [
        "javascript:alert(1)", "data:text/html,<script>", " javascript:x",
    ])
    def test_unsichere_adressen_werden_verworfen(self, boese):
        """Der Wert kommt aus einer Einstellung und landet in einem `href`
        auf einer Seite, die ein Kunde oeffnet."""
        d = _daten(bericht_kauf_relaunch_url=boese,
                   widget_check_plus_url=boese)
        assert not d["kaufUrlRelaunch"].startswith(("javascript:", "data:"))
        assert not d["kaufUrlCheckPlus"].startswith(("javascript:", "data:"))
