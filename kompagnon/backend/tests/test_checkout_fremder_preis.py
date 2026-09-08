# -*- coding: utf-8 -*-
"""Der Checkout ueberlebt eine Preis-ID aus dem alten Stripe-Konto.

**Am Gegenstand geprueft, nicht an den Helfern.** `stripe_fremd` hat eigene
Tests; sie sagen nichts darueber, ob der Rueckfall im Bezahlweg auch
angeschlossen ist. Genau das ist die Luecke, die hier zugeht — geprueft wird
`POST /api/payments/create-checkout` mit einem Produkt, dessen gespeicherte
Preis-ID nicht zum verbundenen Konto gehoert.

**Beide Richtungen.** Der Rueckfall muss greifen, wenn der Preis fehlt — und
er darf **nicht** greifen, wenn Stripe etwas anderes meldet. Ohne die zweite
Haelfte verwandelte er eine abgelehnte Karte oder einen falschen Schluessel
in einen erfolgreichen Checkout.
"""
import uuid

import pytest
import stripe
from sqlalchemy import text


class FalscheSitzung:
    url = "https://checkout.stripe.test/c/pay/cs_test_x"
    id = "cs_test_x"


@pytest.fixture()
def paket(app):
    """Ein lebendes Produkt mit einer Preis-ID aus einem fremden Konto."""
    from database import SessionLocal

    slug = f"pruefpaket-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  status, stripe_price_id)
            VALUES (:s, 'Pruefpaket', 'Nur fuer den Test', 1999.00,
                    'live', 'price_aus_dem_alten_konto')
        """), {"s": slug})
        db.commit()
        yield slug
        db.execute(text("DELETE FROM products WHERE slug=:s"), {"s": slug})
        db.commit()
    finally:
        db.close()


def _anfrage(client, slug):
    return client.post("/api/payments/create-checkout", json={
        "package": slug,
        "email": "pruefung@example.org",
        "name": "Pruef Person",
        "company": "Pruef GmbH",
    })


def test_der_checkout_faellt_auf_den_einzelbetrag_zurueck(
        client, paket, monkeypatch):
    """Die gespeicherte ID fehlt im Konto — der Kunde kommt trotzdem zur Kasse."""
    versuche = []

    def _create(**kwargs):
        posten = kwargs["line_items"][0]
        versuche.append(posten)
        if "price" in posten:
            raise stripe.error.InvalidRequestError(
                "No such price: 'price_aus_dem_alten_konto'",
                param="line_items[0][price]", code="resource_missing")
        return FalscheSitzung()

    monkeypatch.setattr(stripe, "api_key", "sk_test_pruefung")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_create))

    antwort = _anfrage(client, paket)

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["checkout_url"] == FalscheSitzung.url

    # Genau zwei Versuche: erst mit der ID, dann mit dem Betrag. Ein dritter
    # hiesse, dass der Rueckfall selbst wieder eine ID mitschickt.
    assert len(versuche) == 2
    assert versuche[0]["price"] == "price_aus_dem_alten_konto"
    assert "price" not in versuche[1]
    # Der Kunde zahlt, was im Katalog steht — 1999,00 EUR.
    assert versuche[1]["price_data"]["unit_amount"] == 199900


def test_eine_abgelehnte_karte_wird_nicht_zum_erfolg(client, paket, monkeypatch):
    """Die Gegenprobe: Nur `resource_missing` loest den Rueckfall aus."""
    versuche = []

    def _create(**kwargs):
        versuche.append(kwargs["line_items"][0])
        raise stripe.error.CardError("Karte abgelehnt", param=None,
                                     code="card_declined")

    monkeypatch.setattr(stripe, "api_key", "sk_test_pruefung")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(_create))

    antwort = _anfrage(client, paket)

    assert antwort.status_code == 400
    # **Kein zweiter Versuch.** Wer hier erneut anfragt, verdeckt den Fehler
    # und laesst den Kunden zweimal warten.
    assert len(versuche) == 1
