# -*- coding: utf-8 -*-
"""Die Rechnung zu einer Shop-Bestellung (L-100, ORDERS_07 Schritte 3 und 4).

**Geprüft wird im fertigen PDF, nicht am Eingabewörterbuch.** Die Pflichtangaben
nach § 14 UStG müssen auf dem Dokument stehen, das der Käufer bekommt — dass
sie in einem Dict standen, sagt darüber nichts. Deshalb erzeugt der Erzeuger
ohne Kompression, und die Prüfungen suchen die Zeichenfolgen in den Bytes.
Ohne das wäre es dieselbe Sorte Prüfung wie die, die den StripeObject-Fehler
monatelang nicht sah: grün, und am Gegenstand nie gewesen.

**Der Riegel, der wirklich weh täte, ist Reverse-Charge.** Ein Geschäftskunde
mit ausländischer EU-USt-IdNr. bezahlt ohne deutsche Umsatzsteuer, und die
Rechnung muss den Übergang der Steuerschuld ausweisen. ORDERS_07 nimmt das
ausdrücklich **nicht** in diese Ausbaustufe auf, verlangt aber, dass der Fall
**erkannt und abgewiesen** wird — statt falsch abgerechnet. Eine falsche
Rechnung ist teurer als eine fehlende: Sie sieht richtig aus.

**Zehn Jahre Aufbewahrungspflicht.** Rechnungen dürfen nicht auf dem flüchtigen
Dateisystem von Render liegen; sie gehören in denselben Objektspeicher wie die
Produktdateien, unter `invoices/{jahr}/{nummer}.pdf`.
"""
from datetime import date

import pytest
from sqlalchemy import text


@pytest.fixture()
def produkt(app):
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status)
            VALUES ('pytest_rechnung', 'Pytest Workbook', 'p', 149.00,
                    139.25, 7, 'once', 'live')
            ON CONFLICT (slug) DO NOTHING"""))
        db.commit()
    finally:
        db.close()

    yield "pytest_rechnung"

    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        db.query(BookOrder).filter(
            BookOrder.product_slug == "pytest_rechnung").delete(
            synchronize_session=False)
        db.execute(text("DELETE FROM products WHERE slug='pytest_rechnung'"))
        db.execute(text("DELETE FROM invoices WHERE invoice_number LIKE 'KAS-%'"))
        db.execute(text("DELETE FROM invoice_counters"))
        db.commit()
    finally:
        db.close()


def _bestellung(slug, *, nummer="B-2026-5001", geschaeftlich=False,
                ustid="", name="Erika Musterfrau"):
    from database import SessionLocal
    from modelle_buch import BookOrder

    teile = name.split(" ", 1)
    db = SessionLocal()
    try:
        db.add(BookOrder(
            order_number=nummer, variant="katalog", product_slug=slug,
            book_version="", email="kaeufer@example.com",
            first_name=teile[0], last_name=teile[1] if len(teile) > 1 else "",
            company="Musterbetrieb GmbH" if geschaeftlich else "",
            ship_street="Teststr. 1, 56068 Koblenz",
            price_gross_cents=14900, tax_rate=7, shipping_cents=0,
            payment_status="paid", is_business=geschaeftlich,
            buyer_vat_id=ustid,
            credit_valid_until=date.today()))
        db.commit()
        return nummer
    finally:
        db.close()


@pytest.fixture()
def ablage(monkeypatch):
    """Ein Speicher, der mitschreibt, statt nach R2 zu gehen."""
    from services import produktablage

    abgelegt = {}
    monkeypatch.setattr(produktablage, "was_fehlt", lambda: [])
    monkeypatch.setattr(
        produktablage, "ablegen",
        lambda schluessel, daten, art="application/pdf":
            abgelegt.update({schluessel: daten}) or True)
    return abgelegt


def _erzeugen(nummer):
    from database import SessionLocal
    from services import rechnung

    db = SessionLocal()
    try:
        return rechnung.fuer_bestellung(db, nummer)
    finally:
        db.close()


# ── Die Pflichtangaben, im fertigen PDF ──────────────────────────────

class TestPflichtangaben:
    def test_das_pdf_traegt_alle_pflichtangaben(self, produkt, ablage,
                                                monkeypatch):
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)

        # Act
        eintrag, _ = _erzeugen("B-2026-5001")
        pdf = list(ablage.values())[0]

        # Assert — gesucht wird im Dokument, nicht in der Eingabe.
        assert pdf.startswith(b"%PDF")
        for pflicht in (
            b"KOMPAGNON",                 # vollstaendiger Name
            b"Marienfelder",              # Anschrift des Ausstellers
            b"DE317883455",               # USt-IdNr. des Ausstellers
            b"Erika Musterfrau",          # Name des Kaeufers
            b"Teststr. 1",                # Anschrift des Kaeufers
            b"Pytest Workbook",           # Bezeichnung der Leistung
            b"139,25",                    # Nettobetrag
            b"9,75",                      # Steuerbetrag (7 % aus 149,00)
            b"149,00",                    # Bruttobetrag
            b"7",                         # Steuersatz
            b"Leistungsdatum",            # Lieferzeitpunkt
            b"bezahlt",                   # Hinweis auf erfolgte Zahlung
        ):
            assert pflicht in pdf, f"fehlt im PDF: {pflicht!r}"

        assert eintrag["invoice_number"].startswith("KAS-")

    def test_die_rechnungsnummer_steht_auf_dem_dokument(self, produkt, ablage,
                                                       monkeypatch):
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)

        # Act
        eintrag, _ = _erzeugen("B-2026-5001")
        pdf = list(ablage.values())[0]

        # Assert — eine Rechnung ohne ihre Nummer ist keine.
        assert eintrag["invoice_number"].encode() in pdf

    def test_der_betrag_kommt_aus_der_bestellung_nicht_aus_dem_katalog(
            self, produkt, ablage, monkeypatch):
        """Der Katalogpreis kann sich nach dem Kauf geaendert haben. Die
        Rechnung weist aus, was **abgebucht** wurde."""
        # Arrange
        from database import SessionLocal

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)
        db = SessionLocal()
        try:
            db.execute(text(
                "UPDATE products SET price_brutto = 199.00 "
                "WHERE slug = 'pytest_rechnung'"))
            db.commit()
        finally:
            db.close()

        # Act
        eintrag, _ = _erzeugen("B-2026-5001")

        # Assert
        assert eintrag["amount_gross_cents"] == 14900


# ── Reverse-Charge ───────────────────────────────────────────────────

class TestReverseCharge:
    def test_auslaendische_eu_ustid_wird_abgewiesen(self, produkt, ablage,
                                                    monkeypatch):
        """Falsch abgerechnet ist teurer als nicht abgerechnet: Eine falsche
        Rechnung sieht richtig aus."""
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt, nummer="B-2026-5002", geschaeftlich=True,
                    ustid="ATU12345678")

        # Act
        eintrag, grund = _erzeugen("B-2026-5002")

        # Assert
        assert eintrag is None
        assert "reverse" in grund.lower() or "steuerschuld" in grund.lower()
        assert ablage == {}          # nichts abgelegt

    def test_deutsche_ustid_ist_kein_reverse_charge(self, produkt, ablage,
                                                    monkeypatch):
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt, nummer="B-2026-5003", geschaeftlich=True,
                    ustid="DE123456789")

        # Act
        eintrag, _ = _erzeugen("B-2026-5003")

        # Assert
        assert eintrag is not None

    def test_ein_verbraucher_ohne_ustid_geht_normal_durch(self, produkt, ablage,
                                                          monkeypatch):
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt, nummer="B-2026-5004")

        # Act
        eintrag, _ = _erzeugen("B-2026-5004")

        # Assert
        assert eintrag is not None

    def test_leerraum_und_kleinschreibung_taeuschen_den_riegel_nicht(
            self, produkt, ablage, monkeypatch):
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt, nummer="B-2026-5005", geschaeftlich=True,
                    ustid="  fr 12345678901 ")

        # Act
        eintrag, _ = _erzeugen("B-2026-5005")

        # Assert
        assert eintrag is None


# ── Ablage und Wiederholung ──────────────────────────────────────────

class TestAblage:
    def test_die_rechnung_liegt_unter_jahr_und_nummer(self, produkt, ablage,
                                                      monkeypatch):
        """Zehn Jahre aufbewahrungspflichtig — nicht auf dem fluechtigen
        Dateisystem, sondern im Objektspeicher."""
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)

        # Act
        eintrag, _ = _erzeugen("B-2026-5001")

        # Assert
        pfad = list(ablage)[0]
        assert pfad == f"invoices/{date.today().year}/{eintrag['invoice_number']}.pdf"

    def test_zweimal_erzeugen_gibt_keine_zweite_nummer(self, produkt, ablage,
                                                       monkeypatch):
        """Eine zweite Rechnungsnummer fuer denselben Vorgang reisst eine
        Luecke in den Kreis, die niemand erklaeren kann."""
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)
        erste, _ = _erzeugen("B-2026-5001")

        # Act
        zweite, _ = _erzeugen("B-2026-5001")

        # Assert
        assert zweite["invoice_number"] == erste["invoice_number"]

    def test_ohne_eingerichteten_speicher_entsteht_keine_nummer(
            self, produkt, monkeypatch):
        """Sonst waere die Nummer vergeben und die Rechnung nirgends — eine
        Luecke im Kreis, erzeugt von einem Einrichtungsfehler."""
        # Arrange
        from database import SessionLocal
        from services import produktablage

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        monkeypatch.setattr(produktablage, "was_fehlt", lambda: ["R2_BUCKET"])
        _bestellung(produkt)

        # Act
        eintrag, grund = _erzeugen("B-2026-5001")

        # Assert
        assert eintrag is None
        assert "R2_BUCKET" in grund

        db = SessionLocal()
        try:
            offen = db.execute(text(
                "SELECT count(*) FROM invoice_counters")).scalar()
        finally:
            db.close()
        assert offen == 0

    def test_eine_unbezahlte_bestellung_bekommt_keine_rechnung(
            self, produkt, ablage, monkeypatch):
        # Arrange
        from database import SessionLocal
        from modelle_buch import BookOrder

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt, nummer="B-2026-5006")
        db = SessionLocal()
        try:
            e = db.query(BookOrder).filter(
                BookOrder.order_number == "B-2026-5006").first()
            e.payment_status = "created"
            db.commit()
        finally:
            db.close()

        # Act
        eintrag, _ = _erzeugen("B-2026-5006")

        # Assert
        assert eintrag is None


# ── Der Abruf ────────────────────────────────────────────────────────

class TestAbruf:
    def test_die_rechnung_haengt_am_abruf_token(self, client, produkt, ablage,
                                                monkeypatch):
        # Arrange
        from database import SessionLocal
        from modelle_buch import BookOrder
        from services import produktablage

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        monkeypatch.setattr(produktablage, "signierte_adresse",
                            lambda s, sekunden=300: f"https://r2.example/{s}")
        _bestellung(produkt)
        _erzeugen("B-2026-5001")

        db = SessionLocal()
        try:
            e = db.query(BookOrder).filter(
                BookOrder.order_number == "B-2026-5001").first()
            e.download_token = "tok-rechnung"
            from datetime import datetime, timedelta
            e.download_expires_at = datetime.utcnow() + timedelta(days=30)
            db.commit()
        finally:
            db.close()

        # Act
        antwort = client.get(
            "/api/shop/orders/B-2026-5001/invoice?token=tok-rechnung",
            follow_redirects=False)

        # Assert
        assert antwort.status_code == 307
        assert "invoices/" in antwort.headers["location"]

    def test_ohne_token_keine_rechnung(self, client, produkt, ablage,
                                       monkeypatch):
        """Die Rechnung traegt Name und Anschrift des Kaeufers. Sie an der
        Bestellnummer allein herauszugeben waere eine Datenschutzluecke —
        die Nummer steht im Browserverlauf."""
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)
        _erzeugen("B-2026-5001")

        # Act
        antwort = client.get("/api/shop/orders/B-2026-5001/invoice",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code in (401, 403, 404, 422)

    def test_ein_falscher_token_ist_404(self, client, produkt, ablage,
                                        monkeypatch):
        # Arrange
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        _bestellung(produkt)
        _erzeugen("B-2026-5001")

        # Act
        antwort = client.get(
            "/api/shop/orders/B-2026-5001/invoice?token=falsch",
            follow_redirects=False)

        # Assert
        assert antwort.status_code == 404


class TestAngeschlossen:
    """Ein Dienst, den kein Weg ruft, ist die Familie L-55 — fuenfmal
    dagewesen. Deshalb hier durch den echten Auslieferungsweg."""

    def test_die_auslieferung_erzeugt_die_rechnung(self, produkt, ablage,
                                                   monkeypatch):
        # Arrange
        import routers.shop as shop

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        monkeypatch.setattr(shop, "_mail_versenden", lambda *_: True)
        _bestellung(produkt, nummer="B-2026-5010")

        # Act
        shop._auslieferung_anstossen("B-2026-5010")

        # Assert
        assert len(ablage) == 1
        assert list(ablage)[0].startswith("invoices/")

    def test_die_bestaetigung_traegt_den_rechnungslink(self, produkt, ablage,
                                                       monkeypatch):
        # Arrange
        import routers.shop as shop

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        gesehen = {}
        monkeypatch.setattr(shop, "_mail_versenden",
                            lambda an, betreff, html: gesehen.update(html=html)
                            or True)
        _bestellung(produkt, nummer="B-2026-5011")

        # Act
        shop._auslieferung_anstossen("B-2026-5011")

        # Assert
        assert "/invoice?token=" in gesehen["html"]

    def test_eine_gescheiterte_rechnung_haelt_die_auslieferung_nicht_an(
            self, produkt, monkeypatch):
        """Der Kaeufer hat bezahlt. Er kommt an seine Datei, auch wenn die
        Ablage klemmt — die Rechnung holt der Innendienst nach."""
        # Arrange
        import routers.shop as shop
        from services import produktablage

        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        monkeypatch.setattr(produktablage, "was_fehlt", lambda: ["R2_BUCKET"])
        gesehen = {}
        monkeypatch.setattr(shop, "_mail_versenden",
                            lambda an, betreff, html: gesehen.update(an=an)
                            or True)
        _bestellung(produkt, nummer="B-2026-5012")

        # Act — darf nicht werfen
        shop._auslieferung_anstossen("B-2026-5012")

        # Assert
        assert gesehen.get("an") == "kaeufer@example.com"
