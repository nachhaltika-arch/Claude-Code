# -*- coding: utf-8 -*-
"""Das Check-PLUS-Angebot im Teaser kommt aus dem Katalog (10.09.2026).

**Warum ein eigener Dienst und keine Zeilen im Widget.** Der Entwurf traegt
`249 €` als Text und einen festen Stripe-Zahllink im Knopf. Beides im Widget
festzuschreiben waere genau L-29: Der Preis stuende dann an einer weiteren
Stelle neben `products`, und die erste Preisaenderung liefe auseinander — im
Widget, das auf **fremden** Seiten laeuft und dort niemandem auffaellt.

**Drei Regeln, die das Angebot ehrlich halten.**

1. **Kein Knopf ohne Ziel.** Solange das Produkt `draft` ist oder keine
   Kaufadresse hinterlegt wurde, ist `verfuegbar` falsch. Das Widget zeigt
   den Block dann ohne Knopf statt mit einem, der ins Leere fuehrt — die
   Klasse „gebaut, nicht angeschlossen", die hier schon fuenfmal auftrat.
2. **Netto und brutto stehen beide da.** Der Entwurf zeigt „249 € netto",
   die Kasse bucht brutto ab. Genau diese Luecke war L-61: Die Seite schrieb
   „netto, zzgl. MwSt.", belastet wurde der andere Betrag. Wer netto zeigt,
   muss den Zahlbetrag danebenstellen.
3. **Fehlt das Produkt, gibt es kein Angebot.** Kein Rueckfall auf
   Standardwerte: Ein erfundener Preis waere schlimmer als ein fehlender
   Block.
"""
import pytest

from services import check_plus_angebot as cpa


class _Zeile(dict):
    """Eine Katalogzeile, wie `app_settings` sie liest."""


def _produkt(**abweichung):
    zeile = {
        "slug": "check_plus", "name": "Check PLUS", "status": "draft",
        "price_netto": 249.00, "price_brutto": 296.31, "tax_rate": 19,
        "delivery_days": 5, "credit_months": 6, "is_creditable": True,
        "features": ["Vollstaendiges Audit, manuell nachgeprueft",
                     "Auswertungsgespraech, 60 Minuten, per Videokonferenz",
                     "Anrechenbar auf einen Websprint, 6 Monate"],
    }
    zeile.update(abweichung)
    return _Zeile(zeile)


class TestPreis:
    def test_beide_betraege_stehen_da(self):
        a = cpa.aus_zeile(_produkt(), kaufadresse="")
        assert a["preis_netto"] == 249.00
        assert a["preis_brutto"] == 296.31

    def test_der_preis_wird_nirgends_erfunden(self):
        # Die Gegenprobe: Ein anderer Katalogpreis muss durchschlagen.
        a = cpa.aus_zeile(_produkt(price_netto=199.00, price_brutto=236.81),
                          kaufadresse="")
        assert a["preis_netto"] == 199.00
        assert a["preis_brutto"] == 236.81


class TestVerfuegbarkeit:
    def test_entwurf_ist_nicht_kaufbar(self):
        a = cpa.aus_zeile(_produkt(status="draft"), kaufadresse="https://buy.example/x")
        assert a["verfuegbar"] is False

    def test_ohne_kaufadresse_kein_knopf(self):
        a = cpa.aus_zeile(_produkt(status="live"), kaufadresse="")
        assert a["verfuegbar"] is False
        assert a["url"] == ""

    def test_live_und_adresse_ergibt_einen_knopf(self):
        a = cpa.aus_zeile(_produkt(status="live"), kaufadresse="https://buy.example/x")
        assert a["verfuegbar"] is True
        assert a["url"] == "https://buy.example/x"

    def test_nur_sichere_adressen(self):
        # Der Wert kommt aus einer Einstellung und landet in einem href auf
        # fremden Seiten. `javascript:` darf dort nicht ankommen.
        a = cpa.aus_zeile(_produkt(status="live"),
                          kaufadresse="javascript:alert(1)")
        assert a["url"] == ""
        assert a["verfuegbar"] is False


class TestInhalt:
    def test_leistungen_kommen_aus_dem_katalog(self):
        a = cpa.aus_zeile(_produkt(), kaufadresse="")
        assert "Vollstaendiges Audit, manuell nachgeprueft" in a["leistungen"]

    def test_die_anrechnung_steht_nicht_in_der_liste(self):
        # Sie ist im Entwurf ein hervorgehobener Kasten, kein Listenpunkt —
        # sonst steht dasselbe zweimal untereinander.
        a = cpa.aus_zeile(_produkt(), kaufadresse="")
        assert not any("Anrechenbar" in l for l in a["leistungen"])
        assert a["anrechnung_monate"] == 6

    def test_lieferzeit_kommt_mit(self):
        a = cpa.aus_zeile(_produkt(), kaufadresse="")
        assert a["lieferzeit_tage"] == 5

    def test_ohne_produkt_kein_angebot(self):
        assert cpa.aus_zeile(None, kaufadresse="https://buy.example/x") is None
