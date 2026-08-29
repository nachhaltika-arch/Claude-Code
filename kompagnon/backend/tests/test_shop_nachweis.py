# -*- coding: utf-8 -*-
"""Der Nachweis, welche AGB-Fassung ein Käufer akzeptiert hat (L-100, ORDERS_05).

**Nur die technische Hälfte.** ORDERS_05 verlangt außerdem Widerrufsbelehrung
und AGB im Wortlaut. Die gibt es im Bestand **nicht** — nachgesehen am
29.08.2026: `Impressum.jsx` und `Datenschutz.jsx` sind da, AGB und
Widerrufsbelehrung nicht. Der Prompt sagt dazu ausdrücklich: *„Erfinde keine
Rechtstexte — auch keine Platzhalter, die aussehen wie echte Texte."* Also
sind hier keine.

**Was hier gebaut ist, ist das, was die Texte später beweisbar macht.**

Der Punkt, den ORDERS_05 „den Punkt, den fast alle vergessen" nennt: Ändern
sich die AGB, muss nachweisbar bleiben, **welche Fassung** der Käufer
akzeptiert hat. Ohne dieses Feld ist die Zustimmung im Streitfall wertlos.

**Ein Feld, das NULL sein darf, wird NULL sein.** Deshalb ist es kein Feld
allein, sondern ein Riegel: Ohne hinterlegte AGB-Fassung entsteht **keine**
Bestellung. Das ist zugleich die Zusicherung, die die Übersicht in Prosa
verlangt — *vor ORDERS_05 darf nichts live gehen* — nur eben im Code statt in
einem Satz, den jemand lesen müsste.
"""
import pytest


# ── Die Fassung ──────────────────────────────────────────────────────

class TestFassung:
    def test_ohne_hinterlegte_fassung_gibt_es_keine(self, monkeypatch):
        # Arrange
        from services import agb
        monkeypatch.delenv("AGB_FASSUNG", raising=False)

        # Act & Assert
        assert agb.fassung() is None

    def test_hinterlegte_fassung_wird_gelesen(self, monkeypatch):
        # Arrange
        from services import agb
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")

        # Act & Assert
        assert agb.fassung() == "2026-09-01"

    def test_leerraum_gilt_als_nicht_hinterlegt(self, monkeypatch):
        """Sonst stünde in der Bestellung eine Fassung namens „ ", und der
        Riegel unten wäre offen, ohne dass es jemand sähe."""
        # Arrange
        from services import agb
        monkeypatch.setenv("AGB_FASSUNG", "   ")

        # Act & Assert
        assert agb.fassung() is None


# ── Der Riegel ───────────────────────────────────────────────────────

@pytest.fixture()
def probeprodukt(app):
    from sqlalchemy import text

    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status)
            VALUES ('pytest_nachweis', 'Pytest Nachweis', 'Probe',
                    100.00, 93.46, 7, 'once', 'live')
            ON CONFLICT (slug) DO NOTHING"""))
        db.commit()
    finally:
        db.close()

    yield "pytest_nachweis"

    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        db.query(BookOrder).filter(
            BookOrder.product_slug == "pytest_nachweis").delete()
        db.execute(text("DELETE FROM products WHERE slug='pytest_nachweis'"))
        db.commit()
    finally:
        db.close()


def _anfrage(code):
    return {
        "product_code": code,
        "buyer_email": "kaeufer@example.com",
        "buyer_name": "Erika Musterfrau",
        "buyer_address": "Teststr. 1, 56068 Koblenz",
        "is_business": True,
        "terms_accepted": True,
        "withdrawal_waived": True,
    }


class TestRiegel:
    def test_ohne_agb_fassung_keine_bestellung(
            self, client, probeprodukt, monkeypatch):
        """Der Riegel, der «vor ORDERS_05 geht nichts live» durchsetzt."""
        # Arrange
        monkeypatch.delenv("AGB_FASSUNG", raising=False)

        # Act
        antwort = client.post("/api/shop/checkout", json=_anfrage(probeprodukt))

        # Assert — 503, nicht 400: Das ist ein Einrichtungszustand, kein
        # Fehler des Käufers, und die Meldung sagt es.
        assert antwort.status_code == 503

    def test_der_riegel_nennt_die_agb_und_nicht_stripe(
            self, client, probeprodukt, monkeypatch):
        """Sonst sucht jemand einen Stripe-Schlüssel, der längst da ist."""
        # Arrange
        monkeypatch.delenv("AGB_FASSUNG", raising=False)

        # Act
        antwort = client.post("/api/shop/checkout", json=_anfrage(probeprodukt))

        # Assert
        assert "AGB" in antwort.json().get("detail", "")

    def test_riegel_greift_vor_der_bestellung_nicht_danach(
            self, client, probeprodukt, monkeypatch):
        """Eine angelegte Bestellung ohne Fassung wäre genau der Nachweis,
        der im Streitfall fehlt."""
        # Arrange
        from database import SessionLocal
        from modelle_buch import BookOrder

        monkeypatch.delenv("AGB_FASSUNG", raising=False)

        # Act
        client.post("/api/shop/checkout", json=_anfrage(probeprodukt))

        # Assert
        db = SessionLocal()
        try:
            assert db.query(BookOrder).filter(
                BookOrder.product_slug == probeprodukt).count() == 0
        finally:
            db.close()


# ── Was mitgeschrieben wird ──────────────────────────────────────────

class TestMitschrift:
    def test_fassung_und_zeitpunkt_stehen_in_der_bestellung(
            self, app, probeprodukt, monkeypatch):
        # Arrange
        from datetime import datetime

        from database import SessionLocal
        from services import agb, bestellung

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        db = SessionLocal()
        try:
            produkt = bestellung.produkt_holen(db, probeprodukt)

            # Act
            eintrag = bestellung.anlegen(db, _anfrage(probeprodukt), produkt)

            # Assert
            assert eintrag.terms_version == "2026-09-01"
            assert eintrag.terms_accepted_at is not None
            assert (datetime.utcnow() - eintrag.terms_accepted_at).seconds < 60
            assert agb.fassung() == "2026-09-01"
        finally:
            db.close()

    def test_verbraucher_mit_verzicht_bekommt_beide_zeitstempel(
            self, app, probeprodukt, monkeypatch):
        """Im Streitfall zählt, **wann** zugestimmt wurde — beim Verzicht
        genauso wie bei den AGB."""
        # Arrange
        from database import SessionLocal
        from services import bestellung

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        daten = _anfrage(probeprodukt)
        daten.update(is_business=False, withdrawal_waived=True)

        db = SessionLocal()
        try:
            produkt = bestellung.produkt_holen(db, probeprodukt)

            # Act
            eintrag = bestellung.anlegen(db, daten, produkt)

            # Assert
            assert eintrag.terms_accepted_at is not None
            assert eintrag.waiver_accepted is True
            assert eintrag.waiver_accepted_at is not None
        finally:
            db.close()

    def test_geschaeftskunde_bekommt_keinen_verzichtszeitpunkt(
            self, app, probeprodukt, monkeypatch):
        """Ein Geschäftskunde hat kein Widerrufsrecht nach § 355 BGB. Einen
        Verzicht zu protokollieren, den es nicht braucht, behauptet etwas."""
        # Arrange
        from database import SessionLocal
        from services import bestellung

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        daten = _anfrage(probeprodukt)
        daten.update(is_business=True, withdrawal_waived=False)

        db = SessionLocal()
        try:
            produkt = bestellung.produkt_holen(db, probeprodukt)

            # Act
            eintrag = bestellung.anlegen(db, daten, produkt)

            # Assert
            assert eintrag.waiver_accepted is False
            assert eintrag.waiver_accepted_at is None
            assert eintrag.terms_accepted_at is not None
        finally:
            db.close()
