# -*- coding: utf-8 -*-
"""Wann eine Anrechnung verbraucht wird (L-100, ORDERS_08 — Entscheidung David).

**Entschieden am 29.08.2026: bei Annahme des Angebots**, nicht beim Erstellen.
Der Grund ist der Kunde: Verfiele die Anrechnung schon mit dem Angebot, kostete
ein Deal, der nicht zustande kommt, ihn seine 149 € — für nichts.

**Damit entsteht aber ein zweites Risiko, und das ist der Kern dieser Datei.**
Zwischen Angebot und Annahme liegen Wochen. Ohne Vormerkung ließe sich dieselbe
Anrechnung in dieser Zeit einem **zweiten** Angebot beilegen, und bei Annahme
beider wäre sie zweimal abgezogen. Deshalb drei Zustände statt zwei:

    frei  →  vorgemerkt (Angebot)  →  eingelöst (Annahme)
                     ↓
                   frei (verloren)

**Der Rückweg ist der wichtigste Teil.** Ein verlorener Deal muss die
Anrechnung freigeben — sonst hätte die Entscheidung „bei Annahme" genau die
Wirkung, die sie vermeiden sollte, nur verzögert: Die Anrechnung wäre für
immer blockiert, statt sofort verbraucht.

**Eingelöst bleibt eingelöst.** Die Rücknahme einer *Einlösung* erfolgt nur von
Hand mit Protokolleintrag; ein Weg zurück im Code wäre ein Weg, denselben
Betrag zweimal anzurechnen.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text


@pytest.fixture()
def katalog(app):
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status,
                                  is_creditable, credit_months)
            VALUES ('pytest_lauf', 'Pytest Lauf', 'p', 149.00, 139.25, 7,
                    'once', 'live', true, 6)
            ON CONFLICT (slug) DO NOTHING"""))
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        db.query(BookOrder).filter(
            BookOrder.product_slug == "pytest_lauf").delete(
            synchronize_session=False)
        db.execute(text("DELETE FROM products WHERE slug = 'pytest_lauf'"))
        db.commit()
    finally:
        db.close()


def _bestellung(nummer, mail="kaeufer@example.com"):
    from database import SessionLocal
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        db.add(BookOrder(
            order_number=nummer, variant="katalog", product_slug="pytest_lauf",
            book_version="", email=mail, first_name="E", last_name="M",
            price_gross_cents=14900, tax_rate=7, shipping_cents=0,
            payment_status="paid",
            credit_valid_until=date.today() + timedelta(days=180)))
        db.commit()
        return nummer
    finally:
        db.close()


def _deal(titel="Websprint"):
    from database import SessionLocal

    db = SessionLocal()
    try:
        neu = db.execute(text(
            "INSERT INTO deals (title, status) VALUES (:t, 'neu') RETURNING id"
        ), {"t": titel}).scalar()
        db.commit()
        return neu
    finally:
        db.close()


def _lies(nummer):
    from database import SessionLocal
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        return db.query(BookOrder).filter(
            BookOrder.order_number == nummer).first()
    finally:
        db.close()


def _mit_db(fn):
    from database import SessionLocal

    db = SessionLocal()
    try:
        return fn(db)
    finally:
        db.close()


# ── Vormerken ────────────────────────────────────────────────────────

class TestVormerken:
    def test_vormerken_setzt_deal_und_zeitpunkt(self, katalog):
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6001")
        deal = _deal()

        # Act
        _, code, _ = _mit_db(
            lambda db: anrechnung.vormerken(db, "B-2026-6001", deal))

        # Assert
        assert code == 200
        eintrag = _lies("B-2026-6001")
        assert eintrag.credit_reserved_deal_id == deal
        assert eintrag.credit_reserved_at is not None
        # Vorgemerkt ist **nicht** eingelöst — das ist der ganze Punkt.
        assert eintrag.credit_redeemed_deal_id is None

    def test_ein_zweites_angebot_bekommt_sie_nicht(self, katalog):
        """Das Risiko der Entscheidung „bei Annahme": Ohne Vormerkung läge
        dieselbe Anrechnung in zwei offenen Angeboten."""
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6002")
        erster, zweiter = _deal("Erstes Angebot"), _deal("Zweites Angebot")
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6002", erster))

        # Act
        _, code, meldung = _mit_db(
            lambda db: anrechnung.vormerken(db, "B-2026-6002", zweiter))

        # Assert
        assert code == 409
        assert str(erster) in meldung

    def test_derselbe_deal_darf_erneut_vormerken(self, katalog):
        """Wer das Angebot zweimal speichert, soll keinen Fehler sehen."""
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6003")
        deal = _deal()
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6003", deal))

        # Act
        _, code, _ = _mit_db(
            lambda db: anrechnung.vormerken(db, "B-2026-6003", deal))

        # Assert
        assert code == 200

    def test_eine_eingeloeste_laesst_sich_nicht_vormerken(self, katalog):
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6004")
        alt, neu = _deal("Alt"), _deal("Neu")
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6004", alt))
        _mit_db(lambda db: anrechnung.einloesen_fuer_deal(db, alt))

        # Act
        _, code, _ = _mit_db(
            lambda db: anrechnung.vormerken(db, "B-2026-6004", neu))

        # Assert
        assert code == 409


# ── Die Prüfung sieht die Vormerkung ─────────────────────────────────

class TestPruefungMitVormerkung:
    def test_vorgemerkt_verschwindet_aus_der_allgemeinen_pruefung(self, katalog):
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6010")
        deal = _deal()
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6010", deal))

        # Act
        offen = _mit_db(
            lambda db: anrechnung.offene(db, "kaeufer@example.com"))

        # Assert
        assert offen == []

    def test_ihr_eigener_deal_sieht_sie_weiter(self, katalog):
        """Sonst verschwände die Abzugsposition beim erneuten Öffnen des
        Angebots, und jemand legte sie ein zweites Mal an."""
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6011")
        deal = _deal()
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6011", deal))

        # Act
        offen = _mit_db(lambda db: anrechnung.offene(
            db, "kaeufer@example.com", fuer_deal=deal))

        # Assert
        assert [e["order_number"] for e in offen] == ["B-2026-6011"]
        assert offen[0]["vorgemerkt"] is True


# ── Einlösen bei Annahme ─────────────────────────────────────────────

class TestEinloesenBeiAnnahme:
    def test_annahme_loest_alle_vorgemerkten_ein(self, katalog):
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6020")
        _bestellung("B-2026-6021")
        deal = _deal()
        for n in ("B-2026-6020", "B-2026-6021"):
            _mit_db(lambda db, n=n: anrechnung.vormerken(db, n, deal))

        # Act
        gebucht = _mit_db(lambda db: anrechnung.einloesen_fuer_deal(db, deal))

        # Assert
        assert sorted(gebucht) == ["B-2026-6020", "B-2026-6021"]
        for n in ("B-2026-6020", "B-2026-6021"):
            assert _lies(n).credit_redeemed_deal_id == deal
            assert _lies(n).credit_redeemed_at is not None

    def test_ein_deal_ohne_vormerkung_loest_nichts_ein(self, katalog):
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6022")
        deal = _deal()

        # Act
        gebucht = _mit_db(lambda db: anrechnung.einloesen_fuer_deal(db, deal))

        # Assert
        assert gebucht == []
        assert _lies("B-2026-6022").credit_redeemed_deal_id is None

    def test_zweimal_annehmen_bucht_nicht_zweimal(self, katalog):
        """Ein Statuswechsel kann mehrfach ankommen."""
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6023")
        deal = _deal()
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6023", deal))
        _mit_db(lambda db: anrechnung.einloesen_fuer_deal(db, deal))
        vorher = _lies("B-2026-6023").credit_redeemed_at

        # Act
        gebucht = _mit_db(lambda db: anrechnung.einloesen_fuer_deal(db, deal))

        # Assert
        assert gebucht == []
        assert _lies("B-2026-6023").credit_redeemed_at == vorher


# ── Freigeben bei verloren ───────────────────────────────────────────

class TestFreigeben:
    def test_ein_verlorener_deal_gibt_die_anrechnung_frei(self, katalog):
        """Der wichtigste Teil der Entscheidung „bei Annahme": Sonst wäre die
        Anrechnung für immer blockiert statt sofort verbraucht."""
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6030")
        deal = _deal()
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6030", deal))

        # Act
        frei = _mit_db(lambda db: anrechnung.freigeben(db, deal))

        # Assert
        assert frei == ["B-2026-6030"]
        eintrag = _lies("B-2026-6030")
        assert eintrag.credit_reserved_deal_id is None
        assert eintrag.credit_reserved_at is None

        # Und sie steht wieder zur Verfügung.
        offen = _mit_db(lambda db: anrechnung.offene(db, "kaeufer@example.com"))
        assert [e["order_number"] for e in offen] == ["B-2026-6030"]

    def test_eine_eingeloeste_wird_nicht_freigegeben(self, katalog):
        """Eingelöst bleibt eingelöst — die Rücknahme ist Handarbeit."""
        # Arrange
        from services import anrechnung

        _bestellung("B-2026-6031")
        deal = _deal()
        _mit_db(lambda db: anrechnung.vormerken(db, "B-2026-6031", deal))
        _mit_db(lambda db: anrechnung.einloesen_fuer_deal(db, deal))

        # Act
        frei = _mit_db(lambda db: anrechnung.freigeben(db, deal))

        # Assert
        assert frei == []
        assert _lies("B-2026-6031").credit_redeemed_deal_id == deal


# ── Am Deal-Endpunkt, nicht nur am Dienst ────────────────────────────

class TestAmEndpunkt:
    """Ein Dienst, den kein Weg aufruft, ist die Familie L-55 — fünfmal
    dagewesen. Deshalb hier durch die echte Route."""

    def test_status_gewonnen_loest_ein(self, client, auth_headers, katalog):
        # Arrange
        _bestellung("B-2026-6040")
        deal = _deal()
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"credit_order_numbers": ["B-2026-6040"]})
        assert _lies("B-2026-6040").credit_reserved_deal_id == deal

        # Act
        antwort = client.put(f"/api/deals/{deal}", headers=auth_headers,
                             json={"status": "gewonnen"})

        # Assert
        assert antwort.status_code == 200
        assert _lies("B-2026-6040").credit_redeemed_deal_id == deal

    def test_status_verloren_gibt_frei(self, client, auth_headers, katalog):
        # Arrange
        _bestellung("B-2026-6041")
        deal = _deal()
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"credit_order_numbers": ["B-2026-6041"]})

        # Act
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"status": "verloren"})

        # Assert
        eintrag = _lies("B-2026-6041")
        assert eintrag.credit_reserved_deal_id is None
        assert eintrag.credit_redeemed_deal_id is None

    def test_eine_entfernte_abzugsposition_gibt_frei(
            self, client, auth_headers, katalog):
        """Wer die Position aus dem Angebot nimmt, soll die Anrechnung
        zurückbekommen — sonst blockiert ein Klick sie sechs Monate."""
        # Arrange
        _bestellung("B-2026-6042")
        deal = _deal()
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"credit_order_numbers": ["B-2026-6042"]})

        # Act — leere Liste heisst „keine mehr", nicht „nichts geaendert"
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"credit_order_numbers": []})

        # Assert
        assert _lies("B-2026-6042").credit_reserved_deal_id is None

    def test_ohne_das_feld_bleibt_die_vormerkung_unangetastet(
            self, client, auth_headers, katalog):
        """Ein Titel-Update darf die Anrechnung nicht abräumen. `None` und
        `[]` sind zwei verschiedene Aussagen."""
        # Arrange
        _bestellung("B-2026-6043")
        deal = _deal()
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"credit_order_numbers": ["B-2026-6043"]})

        # Act
        client.put(f"/api/deals/{deal}", headers=auth_headers,
                   json={"title": "Anderer Titel"})

        # Assert
        assert _lies("B-2026-6043").credit_reserved_deal_id == deal

    def test_auch_beim_anlegen_wird_vorgemerkt(self, client, auth_headers,
                                               katalog):
        """Beim Anlegen gibt es die Deal-Nummer erst nach dem Einfuegen —
        also wird danach vorgemerkt, nicht davor."""
        # Arrange
        _bestellung("B-2026-6044")

        # Act
        antwort = client.post("/api/deals/", headers=auth_headers, json={
            "title": "Neuer Websprint",
            "credit_order_numbers": ["B-2026-6044"],
        })

        # Assert
        assert antwort.status_code in (200, 201)
        neu = antwort.json()["id"]
        assert _lies("B-2026-6044").credit_reserved_deal_id == neu
        assert _lies("B-2026-6044").credit_redeemed_deal_id is None
