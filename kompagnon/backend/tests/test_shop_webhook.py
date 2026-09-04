# -*- coding: utf-8 -*-
"""Die Zahlungsrückmeldung für Katalogprodukte (L-100, ORDERS_04).

**Warum nicht die Erfolgsseite den Status setzt.** Ihre Adresse steht im
Browser; wer sie aufruft, ohne bezahlt zu haben, bekäme sonst die Ware. Nur
die Meldung von Stripe ist belastbar.

**Der Fund, der diesen Schritt dringend macht.** `zahlungsweg.weg_der_sitzung`
schickte **jede** Sitzung mit einer Bestellnummer zum Buch — und Shop-Kassen
tragen seit ORDERS_03 ebenfalls eine. Ein gekauftes Workbook wäre im
Buch-Pfad gelandet, dort auf `paid` gesetzt und dann durch
`ist_digital` gefallen: `variant` ist `"katalog"`, nicht `"pdf"` oder
`"bundle"`. **Kein Abruf-Token, keine Auslieferung** — bezahlt und nichts
bekommen. Aufgefallen ist es nicht im Betrieb, weil die drei Katalogprodukte
bis ORDERS_05 auf `draft` stehen; der Fehler lag bereit, nicht offen.

**Eigenes Signaturgeheimnis, kein geteiltes** (L-138, 27.08.2026). Ein neuer
Stripe-Endpunkt bekommt ein eigenes Secret; das des Buchs prüft die Signatur
dieser Adresse nicht.

**Immer HTTP 200, außer bei ungültiger Signatur.** Ein Fehlercode lässt Stripe
denselben Vorgang tagelang erneut senden.
"""
import pytest


# ── Die Weiche ───────────────────────────────────────────────────────

class TestZahlungsweg:
    """Vier Wege statt drei — und der Shop darf nicht mehr Buch heissen."""

    def test_shop_sitzung_gehoert_zum_shop(self):
        # Arrange
        from services.zahlungsweg import SHOP, weg_der_sitzung

        # Act
        weg = weg_der_sitzung({"order_number": "B-2026-0001",
                               "product_code": "workbook_homepage_standard"})

        # Assert
        assert weg == SHOP

    def test_buch_sitzung_bleibt_beim_buch(self):
        # Arrange
        from services.zahlungsweg import BUCH, weg_der_sitzung

        # Act
        weg = weg_der_sitzung({"order_number": "HS-2026-0001",
                               "variant": "pdf", "book_version": "1.0"})

        # Assert
        assert weg == BUCH

    def test_geo_und_websprint_unveraendert(self):
        # Arrange
        from services.zahlungsweg import GEO, WEBSPRINT, weg_der_sitzung

        # Act & Assert
        assert weg_der_sitzung({"addon_type": "geo"}) == GEO
        assert weg_der_sitzung({"package": "starter"}) == WEBSPRINT
        assert weg_der_sitzung(None) == WEBSPRINT

    def test_buch_pfad_verarbeitet_keine_shop_sitzung(self):
        """Der eigentliche Befund: ohne diese Trennung setzt der Buch-Pfad
        eine Shop-Bestellung auf bezahlt und liefert nie aus."""
        # Arrange
        from services.zahlungsweg import BUCH, gehoert_hierher

        # Act
        gehoert = gehoert_hierher(BUCH, {"order_number": "B-2026-0001",
                                         "product_code": "check_plus"})

        # Assert
        assert gehoert is False


# ── Der Endpunkt ─────────────────────────────────────────────────────

@pytest.fixture()
def geheimnis(monkeypatch):
    monkeypatch.setenv("SHOP_STRIPE_WEBHOOK_SECRET", "whsec_pytest")
    return "whsec_pytest"


def _ereignis(nummer, betrag_cents, art="checkout.session.completed"):
    return {
        "type": art,
        "data": {"object": {
            "id": "cs_test_123",
            "payment_intent": "pi_test_456",
            "amount_total": betrag_cents,
            "metadata": {"order_number": nummer, "product_code": "pytest_probeprodukt"},
        }},
    }


@pytest.fixture()
def bestellung(app):
    """Eine offene Shop-Bestellung — und danach wieder weg."""
    from sqlalchemy import text

    from database import SessionLocal
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status)
            VALUES ('pytest_probeprodukt', 'Pytest Probeprodukt', 'Probe',
                    100.00, 93.46, 7, 'once', 'live')
            ON CONFLICT (slug) DO NOTHING"""))
        eintrag = BookOrder(
            order_number="B-2026-9001", variant="katalog",
            product_slug="pytest_probeprodukt", book_version="",
            email="kaeufer@example.com", first_name="Erika", last_name="M",
            price_gross_cents=10000, tax_rate=7, shipping_cents=0,
            payment_status="created", stripe_session_id="cs_test_123")
        db.add(eintrag)
        db.commit()
    finally:
        db.close()

    yield "B-2026-9001"

    db = SessionLocal()
    try:
        db.query(BookOrder).filter(
            BookOrder.product_slug == "pytest_probeprodukt").delete()
        db.execute(text("DELETE FROM products WHERE slug='pytest_probeprodukt'"))
        db.commit()
    finally:
        db.close()


def _stand(nummer):
    from database import SessionLocal
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        e = db.query(BookOrder).filter(BookOrder.order_number == nummer).first()
        return (e.payment_status, e.stripe_payment_intent) if e else (None, None)
    finally:
        db.close()


class TestSignatur:
    def test_ohne_gueltige_signatur_400(self, client, geheimnis):
        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "unsinn"})

        # Assert
        assert antwort.status_code == 400

    def test_ohne_eingerichtetes_geheimnis_400(self, client, monkeypatch):
        """Nicht 200: Eine nicht eingerichtete Adresse soll auffallen,
        nicht stillschweigend jede Meldung schlucken."""
        # Arrange
        monkeypatch.delenv("SHOP_STRIPE_WEBHOOK_SECRET", raising=False)

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "egal"})

        # Assert
        assert antwort.status_code == 400


class TestVerbuchen:
    def test_bezahlt_setzt_status_und_zahlungskennung(
            self, client, geheimnis, bestellung, monkeypatch):
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_ereignis_pruefen",
                            lambda *_: _ereignis(bestellung, 10000))

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "gut"})

        # Assert
        assert antwort.status_code == 200
        assert _stand(bestellung) == ("paid", "pi_test_456")

    def test_zweite_zustellung_aendert_nichts(
            self, client, geheimnis, bestellung, monkeypatch):
        """Stripe sendet bei Zweifeln erneut. Ohne diese Prüfung gäbe es
        doppelte Rechnung und doppelte Mail."""
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_ereignis_pruefen",
                            lambda *_: _ereignis(bestellung, 10000))
        client.post("/api/shop/webhook", content=b"{}",
                    headers={"stripe-signature": "gut"})

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "gut"})

        # Assert
        assert antwort.status_code == 200
        assert _stand(bestellung) == ("paid", "pi_test_456")

    def test_abweichender_betrag_wird_nicht_verbucht(
            self, client, geheimnis, bestellung, monkeypatch):
        """Ein anderer Betrag als bestellt ist eine Auffälligkeit, kein Kauf."""
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_ereignis_pruefen",
                            lambda *_: _ereignis(bestellung, 100))

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "gut"})

        # Assert
        assert antwort.status_code == 200
        assert _stand(bestellung)[0] == "created"

    def test_unbekannte_bestellung_bleibt_200(
            self, client, geheimnis, monkeypatch):
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_ereignis_pruefen",
                            lambda *_: _ereignis("B-2026-9999", 10000))

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "gut"})

        # Assert
        assert antwort.status_code == 200

    def test_andere_ereignisart_wird_quittiert_und_ignoriert(
            self, client, geheimnis, bestellung, monkeypatch):
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_ereignis_pruefen",
                            lambda *_: _ereignis(bestellung, 10000,
                                                 art="payment_intent.created"))

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "gut"})

        # Assert
        assert antwort.status_code == 200
        assert _stand(bestellung)[0] == "created"

    def test_fremder_weg_wird_nicht_angefasst(
            self, client, geheimnis, bestellung, monkeypatch):
        """Jeder Stripe-Endpunkt bekommt jede Kasse des Kontos. Eine
        Buch-Sitzung darf hier nichts auslösen."""
        # Arrange
        import routers.shop as shop
        fremd = _ereignis(bestellung, 10000)
        fremd["data"]["object"]["metadata"] = {
            "order_number": bestellung, "variant": "pdf", "book_version": "1.0"}
        monkeypatch.setattr(shop, "_ereignis_pruefen", lambda *_: fremd)

        # Act
        antwort = client.post("/api/shop/webhook", content=b"{}",
                              headers={"stripe-signature": "gut"})

        # Assert
        assert antwort.status_code == 200
        assert _stand(bestellung)[0] == "created"


# ── Die Statusauskunft ───────────────────────────────────────────────

class TestStatusauskunft:
    def test_gibt_nur_nummer_status_und_produkt(self, client, bestellung):
        # Act
        antwort = client.get(f"/api/shop/orders/{bestellung}/status")

        # Assert
        assert antwort.status_code == 200
        assert set(antwort.json()) == {"order_number", "status", "product_code"}

    def test_verraet_weder_mail_noch_betrag_noch_anschrift(
            self, client, bestellung):
        """Die Bestellnummer steht im Browserverlauf und in Mails; sie ist
        kein Geheimnis. Wer hier den vollen Datensatz ausliefert, baut eine
        Datenschutzlücke."""
        # Act
        roh = client.get(f"/api/shop/orders/{bestellung}/status").text

        # Assert
        assert "kaeufer@example.com" not in roh
        assert "Erika" not in roh
        assert "10000" not in roh

    def test_unbekannte_nummer_404(self, client):
        # Act
        antwort = client.get("/api/shop/orders/B-2026-9999/status")

        # Assert
        assert antwort.status_code == 404
