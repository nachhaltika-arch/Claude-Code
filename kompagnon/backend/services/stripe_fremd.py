# -*- coding: utf-8 -*-
"""Gespeicherte Stripe-IDs, die nicht zum verbundenen Konto gehoeren.

**Der Anlass (08.09.2026).** Websprint bekommt ein eigenes Stripe-Konto,
getrennt von KOMPAGNON. Schluessel und Webhook-Geheimnisse lassen sich
tauschen — **Objekte nicht**: Preise, Produkte, Kunden und Abonnements
gehoeren jeweils genau einem Konto.

In `products.stripe_price_id` und `products.stripe_product_id` stehen die
IDs, die der Knopf „nach Stripe spiegeln" hinterlassen hat. Nach dem Wechsel
zeigen sie ins Leere — an der teuersten Stelle: Der Kunde klickt „Jetzt
kaufen" und liest *„No such price"*, obwohl alles richtig eingerichtet ist.

**Der Rueckfall ist ehrlich, nicht bequem.** Er baut denselben Betrag als
Einzelposten (`price_data`), den der Checkout ohnehin baut, wenn gar keine
Preis-ID hinterlegt ist — der Kunde zahlt also genau, was im Katalog steht.
Was er nicht tut: die veraltete ID stillschweigend korrigieren. Wer sie
loeschen will, tut das im Werkzeug; hier wird sie **protokolliert**, damit
sie auffaellt.
"""
import logging

logger = logging.getLogger(__name__)

#: Stripes Zusage fuer „dieses Objekt gibt es in diesem Konto nicht".
#:
#: **Am Code und nicht am Text.** Die Meldung lautet „No such price:
#: 'price_123'" und ist englischer Fliesstext, der sich mit jeder Version
#: aendern darf. `code` ist die dokumentierte Zusage.
FEHLT = "resource_missing"


def objekt_fehlt(fehler) -> bool:
    """Ist das der Fehler „diese ID gibt es in diesem Konto nicht"?

    **Eng gefasst mit Absicht.** Wuerde hier auch eine abgelehnte Karte oder
    ein ungueltiger Schluessel durchgehen, verwandelte der Rueckfall einen
    echten Fehler in ein Ergebnis — und niemand saehe je, dass Stripe gar
    nicht erreichbar war.
    """
    import stripe

    if not isinstance(fehler, stripe.error.InvalidRequestError):
        return False
    return getattr(fehler, "code", None) == FEHLT


def einzelposten(name: str, beschreibung: str, betrag_cents: int) -> dict:
    """Ein Checkout-Posten aus dem Betrag statt aus einer Preis-ID.

    :raises ValueError: bei einem Betrag unter null — ein Checkout, der Geld
        zurueckgibt, waere schlimmer als einer, der nicht zustande kommt.
    """
    if betrag_cents < 0:
        raise ValueError(f"Betrag unter null: {betrag_cents} Cent")

    produkt = {"name": name}
    # Stripe weist `description: ""` zurueck. Ein Rueckfall, der selbst
    # scheitert, ist keiner.
    if (beschreibung or "").strip():
        produkt["description"] = beschreibung

    return {
        "price_data": {
            "currency": "eur",
            "product_data": produkt,
            "unit_amount": betrag_cents,
        },
        "quantity": 1,
    }


def melde_veraltete_id(art: str, kennung: str, slug: str) -> None:
    """Ins Protokoll, damit die veraltete ID nicht unsichtbar weiterlebt.

    `logger.warning` und nicht `info`: Es ist kein Normalzustand, sondern ein
    Rest aus einem anderen Konto — er gehoert im Werkzeug entfernt.
    """
    logger.warning(
        "Stripe: %s %s (Produkt '%s') gehoert nicht zum verbundenen Konto — "
        "Rueckfall auf den Einzelbetrag. Die gespeicherte ID stammt aus einem "
        "anderen Konto und sollte im Werkzeug neu gespiegelt werden.",
        art, kennung, slug)
