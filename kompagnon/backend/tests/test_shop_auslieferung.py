# -*- coding: utf-8 -*-
"""Nach der Zahlung: Abruf-Link und Bestätigungsmail (L-100, ORDERS_06).

**Der Stumpf ist ab jetzt echt.** In ORDERS_04 stand hier ein Protokolleintrag
„Auslieferung steht aus" — bewusst, weil an genau dieser Stelle in diesem
Bestand fünfmal etwas gebaut und nie angeschlossen wurde.

**Was der Käufer bekommt, ist nicht die signierte Adresse.** Er bekommt einen
Abruf-Link auf uns, der dreißig Tage gilt; die signierte R2-Adresse entsteht
erst beim Klick und lebt Minuten. Andersherum stünde eine Adresse, die
Monate gilt, dauerhaft im Postfach und in jedem Mailarchiv.

**Ein unbekannter und ein unbezahlter Abruf sehen gleich aus.** Beide 404.
Wer den Unterschied sehen kann, kann Bestellnummern durchprobieren und
erfährt, welche existieren.

**Und ein abgelaufener Link ist keins von beidem** — er bekommt eine eigene
Auskunft, sonst schreibt ein Käufer, dessen Frist um ist, eine Beschwerde über
einen Link, der „nicht funktioniert".
"""
from datetime import datetime, timedelta

import pytest


@pytest.fixture()
def produkt_mit_datei(app):
    from sqlalchemy import text

    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status,
                                  delivery_type, delivery_key)
            VALUES ('pytest_lieferbar', 'Pytest Lieferbar', 'Probe',
                    100.00, 93.46, 7, 'once', 'live', 'download',
                    'produkte/pytest.pdf')
            ON CONFLICT (slug) DO UPDATE SET delivery_key = 'produkte/pytest.pdf'
            """))
        db.commit()
    finally:
        db.close()

    yield "pytest_lieferbar"

    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        db.query(BookOrder).filter(
            BookOrder.product_slug == "pytest_lieferbar").delete()
        db.execute(text("DELETE FROM products WHERE slug='pytest_lieferbar'"))
        db.commit()
    finally:
        db.close()


def _bestellung(slug, *, status="paid", token="tok-pytest-1",
                ablauf_tage=30, nummer="B-2026-8001", abrufe=0):
    from database import SessionLocal
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        eintrag = BookOrder(
            order_number=nummer, variant="katalog", product_slug=slug,
            book_version="", email="kaeufer@example.com",
            first_name="Erika", last_name="M",
            price_gross_cents=10000, tax_rate=7, shipping_cents=0,
            payment_status=status, download_token=token,
            download_count=abrufe,
            download_expires_at=datetime.utcnow() + timedelta(days=ablauf_tage))
        db.add(eintrag)
        db.commit()
        return nummer
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


# ── Der Abruf ────────────────────────────────────────────────────────

@pytest.fixture()
def ablage(monkeypatch):
    """Ein eingerichteter Speicher, ohne echte Zugangsdaten."""
    from services import produktablage as dateiablage

    monkeypatch.setattr(dateiablage, "was_fehlt", lambda: [])
    monkeypatch.setattr(dateiablage, "signierte_adresse",
                        lambda schluessel, sekunden=300:
                        f"https://r2.example/{schluessel}?sig=x")


class TestAbruf:
    def test_bezahlter_abruf_leitet_auf_die_signierte_adresse(
            self, client, produkt_mit_datei, ablage):
        # Arrange
        _bestellung(produkt_mit_datei, token="tok-gut")

        # Act
        antwort = client.get("/api/shop/download/tok-gut",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 307
        assert antwort.headers["location"].startswith(
            "https://r2.example/produkte/pytest.pdf")

    def test_jeder_abruf_wird_gezaehlt(self, client, produkt_mit_datei, ablage):
        """Ohne Zählwerk lässt sich später nicht sagen, ob ein Link
        weitergegeben wurde."""
        # Arrange
        nummer = _bestellung(produkt_mit_datei, token="tok-zaehl")

        # Act
        client.get("/api/shop/download/tok-zaehl", follow_redirects=False)
        client.get("/api/shop/download/tok-zaehl", follow_redirects=False)

        # Assert
        assert _lies(nummer).download_count == 2

    def test_der_zaehler_begrenzt_auch(self, client, produkt_mit_datei, ablage):
        """**Ein Zaehler ohne Grenze ist eine Zahl, keine Begrenzung.**

        Gefunden am 31.08.2026 (L-105): `download_count` lief seit dem Bau der
        Auslieferung mit und wurde **nirgends geprueft**. Im Datensatz sah das
        aus wie eine Beschraenkung; in Wirklichkeit liess sich dieselbe Datei
        beliebig oft holen — auch von jedem, der den Link weitergereicht bekam.
        BUCH-06 verlangt hoechstens fuenf.
        """
        from routers.shop import ABRUFE_HOECHSTENS

        # Arrange — die Grenze ist erreicht
        _bestellung(produkt_mit_datei, token="tok-voll", abrufe=ABRUFE_HOECHSTENS)

        # Act
        antwort = client.get("/api/shop/download/tok-voll",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 410
        assert str(ABRUFE_HOECHSTENS) in antwort.json()["detail"]

    def test_der_letzte_erlaubte_abruf_geht_noch_durch(
            self, client, produkt_mit_datei, ablage):
        """Die Gegenprobe zur Grenze.

        Ohne sie waere der Test darueber auch dann gruen, wenn die Grenze bei
        null laege und **kein** Kaeufer je seine Datei bekaeme.
        """
        from routers.shop import ABRUFE_HOECHSTENS

        # Arrange — einer ist noch frei
        _bestellung(produkt_mit_datei, token="tok-letzter",
                    abrufe=ABRUFE_HOECHSTENS - 1)

        # Act
        antwort = client.get("/api/shop/download/tok-letzter",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 307

    def test_ein_abgewiesener_abruf_zaehlt_nicht_weiter(
            self, client, produkt_mit_datei, ablage):
        """Sonst waechst der Zaehler bei jedem Versuch, und die Auskunft
        „bereits 5 Mal benutzt" wuerde bei 40 Versuchen zur Luege."""
        from routers.shop import ABRUFE_HOECHSTENS

        # Arrange
        nummer = _bestellung(produkt_mit_datei, token="tok-nachzaehlen",
                             abrufe=ABRUFE_HOECHSTENS)

        # Act
        client.get("/api/shop/download/tok-nachzaehlen", follow_redirects=False)
        client.get("/api/shop/download/tok-nachzaehlen", follow_redirects=False)

        # Assert
        assert _lies(nummer).download_count == ABRUFE_HOECHSTENS

    def test_unbekannter_abruf_ist_404(self, client, ablage):
        # Act
        antwort = client.get("/api/shop/download/gibt-es-nicht",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 404

    def test_unbezahlter_abruf_sieht_aus_wie_ein_unbekannter(
            self, client, produkt_mit_datei, ablage):
        """Sonst verrät der Unterschied, welche Bestellnummern es gibt."""
        # Arrange
        _bestellung(produkt_mit_datei, status="created", token="tok-offen")

        # Act
        antwort = client.get("/api/shop/download/tok-offen",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 404

    def test_abgelaufener_abruf_bekommt_eine_eigene_auskunft(
            self, client, produkt_mit_datei, ablage):
        # Arrange
        _bestellung(produkt_mit_datei, token="tok-alt", ablauf_tage=-1)

        # Act
        antwort = client.get("/api/shop/download/tok-alt",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 410
        assert "abgelaufen" in antwort.json()["detail"].lower()

    def test_abgelaufener_abruf_wird_nicht_mitgezaehlt(
            self, client, produkt_mit_datei, ablage):
        # Arrange
        nummer = _bestellung(produkt_mit_datei, token="tok-alt2", ablauf_tage=-1)

        # Act
        client.get("/api/shop/download/tok-alt2", follow_redirects=False)

        # Assert
        assert _lies(nummer).download_count == 0

    def test_ohne_eingerichteten_speicher_503_statt_500(
            self, client, produkt_mit_datei, monkeypatch):
        """Der Käufer hat bezahlt. „Interner Serverfehler" ist keine Auskunft."""
        # Arrange
        from services import produktablage as dateiablage
        monkeypatch.setattr(dateiablage, "was_fehlt", lambda: ["R2_BUCKET"])
        _bestellung(produkt_mit_datei, token="tok-ohne-speicher")

        # Act
        antwort = client.get("/api/shop/download/tok-ohne-speicher",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 503

    def test_produkt_ohne_hinterlegte_datei_ist_503(
            self, client, app, ablage):
        """Nicht 404: Die Bestellung gibt es, die Datei fehlt bei uns."""
        # Arrange
        from sqlalchemy import text

        from database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text("""
                INSERT INTO products (slug, name, short_desc, price_brutto,
                                      price_netto, tax_rate, payment_type,
                                      status, delivery_type)
                VALUES ('pytest_ohne_datei', 'Ohne Datei', 'Probe',
                        100.00, 93.46, 7, 'once', 'live', 'download')
                ON CONFLICT (slug) DO NOTHING"""))
            db.commit()
        finally:
            db.close()
        _bestellung("pytest_ohne_datei", token="tok-ohne-datei",
                    nummer="B-2026-8009")

        # Act
        antwort = client.get("/api/shop/download/tok-ohne-datei",
                             follow_redirects=False)

        # Assert
        assert antwort.status_code == 503

        db = SessionLocal()
        try:
            from modelle_buch import BookOrder
            db.query(BookOrder).filter(
                BookOrder.product_slug == "pytest_ohne_datei").delete()
            db.execute(text(
                "DELETE FROM products WHERE slug='pytest_ohne_datei'"))
            db.commit()
        finally:
            db.close()


# ── Die Auslieferung nach der Zahlung ────────────────────────────────

class TestAuslieferung:
    def test_auslieferung_vergibt_token_und_frist(
            self, app, produkt_mit_datei, monkeypatch):
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_bestaetigung_senden", lambda *_: True)
        nummer = _bestellung(produkt_mit_datei, token=None,
                             nummer="B-2026-8002")

        # Act
        shop._auslieferung_anstossen(nummer)

        # Assert
        eintrag = _lies(nummer)
        assert eintrag.download_token
        assert eintrag.download_expires_at > datetime.utcnow()
        assert eintrag.delivered_at is not None

    def test_zweimal_ausliefern_erzeugt_keinen_zweiten_token(
            self, app, produkt_mit_datei, monkeypatch):
        """Stripe stellt mehrfach zu. Ein zweiter Token machte den Link aus
        der ersten Mail still ungültig."""
        # Arrange
        import routers.shop as shop
        monkeypatch.setattr(shop, "_bestaetigung_senden", lambda *_: True)
        nummer = _bestellung(produkt_mit_datei, token=None,
                             nummer="B-2026-8003")
        shop._auslieferung_anstossen(nummer)
        erster = _lies(nummer).download_token

        # Act
        shop._auslieferung_anstossen(nummer)

        # Assert
        assert _lies(nummer).download_token == erster

    def test_die_mail_traegt_den_abruf_link_und_die_fassung(
            self, app, produkt_mit_datei, monkeypatch):
        """ORDERS_05 Schritt 4: Der Wortlaut der akzeptierten Erklärungen
        wird in der Bestätigung wiederholt."""
        # Arrange
        import routers.shop as shop
        monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")
        gesehen = {}
        monkeypatch.setattr(shop, "_mail_versenden",
                            lambda an, betreff, html: gesehen.update(
                                an=an, betreff=betreff, html=html) or True)
        nummer = _bestellung(produkt_mit_datei, token=None,
                             nummer="B-2026-8004")

        # Act
        shop._auslieferung_anstossen(nummer)

        # Assert
        assert gesehen["an"] == "kaeufer@example.com"
        assert "/api/shop/download/" in gesehen["html"]
        assert "2026-09-01" in gesehen["html"]

    def test_eine_gescheiterte_mail_nimmt_die_zahlung_nicht_mit(
            self, app, produkt_mit_datei, monkeypatch):
        """Am 26.08. riss ein Fehler im Mailanhang den ganzen Versand mit.
        Die Zahlung ist die Hauptsache, die Mail das Beiwerk."""
        # Arrange
        import routers.shop as shop

        def kaputt(*_args, **_kwargs):
            raise RuntimeError("Brevo antwortet nicht")

        monkeypatch.setattr(shop, "_mail_versenden", kaputt)
        nummer = _bestellung(produkt_mit_datei, token=None,
                             nummer="B-2026-8005")

        # Act — darf nicht werfen
        shop._auslieferung_anstossen(nummer)

        # Assert: Der Token ist trotzdem da, der Käufer kommt an seine Datei.
        assert _lies(nummer).download_token
