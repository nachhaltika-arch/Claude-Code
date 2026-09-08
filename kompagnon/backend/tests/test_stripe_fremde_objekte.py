# -*- coding: utf-8 -*-
"""Gespeicherte Stripe-IDs ueberleben einen Kontowechsel nicht (08.09.2026).

**Der Anlass.** Websprint bekommt ein eigenes Stripe-Konto, getrennt von
KOMPAGNON (Entscheidung David, 08.09.2026). Schluessel und
Webhook-Geheimnisse lassen sich tauschen — **Objekte nicht**: Preise,
Produkte, Kunden und Abonnements gehoeren jeweils genau einem Konto.

In `products.stripe_price_id` und `products.stripe_product_id` stehen die
IDs, die der Knopf „nach Stripe spiegeln" dort hinterlassen hat. Nach dem
Wechsel zeigen sie ins Leere — und zwar an der teuersten Stelle: Der Kunde
klickt „Jetzt kaufen" und bekommt *„No such price"*, obwohl Schluessel,
Webhooks und Steuersatz alle richtig eingerichtet sind.

**Warum am Fehlercode und nicht am Text.** Stripe schreibt „No such price:
'price_123'" auf Englisch, und dieser Satz ist keine Zusage — er kann sich
mit jeder Version aendern. `code == "resource_missing"` ist die Zusage.

**Warum ueberhaupt hier und nicht einmal von Hand aufgeraeumt.** Die Spalten
liessen sich mit einem `UPDATE` leeren, und das ist auch richtig. Aber
derselbe Fehler entsteht wieder, wenn jemand einen Preis in Stripe loescht
oder archiviert. Ein Kontowechsel ist der laute Fall; der leise ist der
gefaehrlichere.
"""
import pytest
import stripe

from services import stripe_fremd


def _fehlend(nachricht="No such price: 'price_alt'"):
    """Ein Fehler, wie Stripe ihn bei einem Objekt aus fremdem Konto wirft."""
    return stripe.error.InvalidRequestError(
        nachricht, param="line_items[0][price]", code="resource_missing")


class TestObjektFehlt:
    """`stripe_fremd.objekt_fehlt` — was als „gibt es hier nicht" gilt."""

    def test_resource_missing_ist_der_fall(self):
        assert stripe_fremd.objekt_fehlt(_fehlend()) is True

    def test_ein_anderer_stripe_fehler_ist_es_nicht(self):
        # **Die wichtigere Haelfte.** Wuerde hier True herauskommen, faenge
        # der Rueckfall auch echte Fehler ab — eine abgelehnte Karte oder ein
        # ungueltiger Schluessel wuerden dann stillschweigend zu einem
        # Checkout mit selbstgebautem Preis. Ein Fehler, der sich in ein
        # Ergebnis verwandelt, ist schlimmer als einer, der auffaellt.
        karte = stripe.error.CardError("Karte abgelehnt", param=None,
                                       code="card_declined")
        assert stripe_fremd.objekt_fehlt(karte) is False

    def test_ein_falscher_schluessel_ist_es_nicht(self):
        auth = stripe.error.AuthenticationError("Ungueltiger Schluessel")
        assert stripe_fremd.objekt_fehlt(auth) is False

    def test_ein_gewoehnlicher_fehler_ist_es_nicht(self):
        assert stripe_fremd.objekt_fehlt(ValueError("irgendwas")) is False

    def test_ohne_code_wird_nicht_geraten(self):
        # Ein InvalidRequestError ohne `code` kann alles sein — etwa ein
        # fehlender Pflichtparameter. Raten hiesse, den Rueckfall auf einen
        # Programmierfehler anzuwenden.
        ohne = stripe.error.InvalidRequestError("etwas fehlt", param="mode")
        assert stripe_fremd.objekt_fehlt(ohne) is False


class TestEinzelposten:
    """`stripe_fremd.einzelposten` — der Rueckfall auf den Einzelbetrag."""

    def test_der_betrag_steht_in_cent(self):
        posten = stripe_fremd.einzelposten("Websprint Start", "Kurzbeschreibung",
                                           199900)
        assert posten["price_data"]["unit_amount"] == 199900
        assert posten["price_data"]["currency"] == "eur"
        assert posten["quantity"] == 1

    def test_der_name_kommt_mit(self):
        posten = stripe_fremd.einzelposten("Websprint Start", "kurz", 100)
        assert posten["price_data"]["product_data"]["name"] == "Websprint Start"

    def test_eine_leere_beschreibung_wird_weggelassen(self):
        # Stripe weist `description: ""` mit einem Fehler zurueck. Ein
        # Rueckfall, der selbst scheitert, ist keiner.
        posten = stripe_fremd.einzelposten("Nur Name", "", 100)
        assert "description" not in posten["price_data"]["product_data"]

    def test_ein_betrag_unter_null_ist_ein_fehler(self):
        with pytest.raises(ValueError):
            stripe_fremd.einzelposten("Kaputt", "", -1)
