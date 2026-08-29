# -*- coding: utf-8 -*-
"""Die Anrechnung auf einen Websprint (L-100, ORDERS_08).

**Die Zusage:** Wer ein Workbook für 149 € oder einen Check PLUS für 249 €
gekauft hat und innerhalb von sechs Monaten einen Websprint beauftragt, bekommt
den Betrag vollständig angerechnet.

**Warum das automatisch laufen muss.** Eine Anrechnung, an die jemand denken
muss, wird irgendwann vergessen. Der Kunde erinnert sich immer — und es ist
genau der Moment, in dem er Vertrauen fassen soll. Ein vergessener Abzug im
Angebot kostet mehr als die 149 €.

**Die drei Zusicherungen, an denen wirklich Geld hängt:**

1. **Zweimal einlösen geht nicht.** Sonst wird derselbe Betrag mehrfach
   abgezogen. Die Einlösung ist endgültig; eine Rücknahme nur von Hand.
2. **Adressen werden normalisiert.** „Max@Betrieb.de" und „max@betrieb.de"
   sind derselbe Kunde. Ohne das findet die Prüfung nichts, und der Kunde ruft
   an — mit Recht.
3. **Alle offenen Anrechnungen werden zurückgegeben, nicht die erste.**
   Jemand kann Workbook **und** Check PLUS gekauft haben; das sind zusammen
   398 €. Die Entscheidung gehört einem Menschen, nicht der Reihenfolge einer
   Datenbankabfrage.
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import text


@pytest.fixture()
def katalog(app):
    """Zwei anrechenbare Produkte und eines ohne Anrechnung."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status,
                                  is_creditable, credit_months)
            VALUES
              ('pytest_wb', 'Pytest Workbook', 'p', 149.00, 139.25, 7,
               'once', 'live', true, 6),
              ('pytest_cp', 'Pytest Check PLUS', 'p', 249.00, 209.24, 19,
               'once', 'live', true, 6),
              ('pytest_ohne', 'Pytest Ohne', 'p', 99.00, 83.19, 19,
               'once', 'live', false, 0)
            ON CONFLICT (slug) DO NOTHING"""))
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        db.query(BookOrder).filter(BookOrder.product_slug.in_(
            ["pytest_wb", "pytest_cp", "pytest_ohne"])).delete(
            synchronize_session=False)
        db.execute(text("DELETE FROM products WHERE slug LIKE 'pytest_%'"))
        db.commit()
    finally:
        db.close()


def _bestellung(slug, *, nummer, mail="kaeufer@example.com", status="paid",
                gueltig_tage=180, netto=13925, eingeloest=None):
    from database import SessionLocal
    from modelle_buch import BookOrder

    db = SessionLocal()
    try:
        eintrag = BookOrder(
            order_number=nummer, variant="katalog", product_slug=slug,
            book_version="", email=mail, first_name="E", last_name="M",
            price_gross_cents=netto, tax_rate=7, shipping_cents=0,
            payment_status=status,
            credit_valid_until=(date.today() + timedelta(days=gueltig_tage)
                                if gueltig_tage is not None else None),
            credit_redeemed_deal_id=eingeloest)
        db.add(eintrag)
        db.commit()
        return nummer
    finally:
        db.close()


def _deal(titel="Websprint Probe"):
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


def _pruefe(client, auth_headers, mail):
    return client.get(f"/api/shop/credit-check?email={mail}",
                      headers=auth_headers)


# ── Die Prüfung ──────────────────────────────────────────────────────

class TestPruefung:
    def test_eine_offene_anrechnung_wird_gefunden(
            self, client, auth_headers, katalog):
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7001")

        # Act
        antwort = _pruefe(client, auth_headers, "kaeufer@example.com")

        # Assert
        daten = antwort.json()
        assert antwort.status_code == 200
        assert [e["order_number"] for e in daten["anrechnungen"]] == ["B-2026-7001"]
        assert daten["summe_cents"] == 13925

    def test_grossschreibung_und_leerraum_finden_denselben_kunden(
            self, client, auth_headers, katalog):
        """Ohne Normalisierung findet die Prüfung nichts, und der Kunde ruft an."""
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7002")

        # Act
        antwort = _pruefe(client, auth_headers, "%20KAEUFER@Example.COM%20")

        # Assert
        assert [e["order_number"] for e in antwort.json()["anrechnungen"]] \
            == ["B-2026-7002"]

    def test_alle_offenen_werden_zurueckgegeben_nicht_die_erste(
            self, client, auth_headers, katalog):
        """Workbook und Check PLUS sind zusammen 398 € — die Entscheidung
        gehört einem Menschen."""
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7003", netto=13925)
        _bestellung("pytest_cp", nummer="B-2026-7004", netto=20924)

        # Act
        daten = _pruefe(client, auth_headers, "kaeufer@example.com").json()

        # Assert
        assert len(daten["anrechnungen"]) == 2
        assert daten["summe_cents"] == 13925 + 20924

    def test_eine_abgelaufene_frist_zaehlt_nicht(
            self, client, auth_headers, katalog):
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7005", gueltig_tage=-1)

        # Act
        daten = _pruefe(client, auth_headers, "kaeufer@example.com").json()

        # Assert
        assert daten["anrechnungen"] == []

    def test_eine_unbezahlte_bestellung_zaehlt_nicht(
            self, client, auth_headers, katalog):
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7006", status="created")

        # Act
        daten = _pruefe(client, auth_headers, "kaeufer@example.com").json()

        # Assert
        assert daten["anrechnungen"] == []

    def test_ein_nicht_anrechenbares_produkt_zaehlt_nicht(
            self, client, auth_headers, katalog):
        # Arrange
        _bestellung("pytest_ohne", nummer="B-2026-7007", gueltig_tage=None)

        # Act
        daten = _pruefe(client, auth_headers, "kaeufer@example.com").json()

        # Assert
        assert daten["anrechnungen"] == []

    def test_eine_bereits_eingeloeste_zaehlt_nicht(
            self, client, auth_headers, katalog):
        # Arrange
        deal = _deal()
        _bestellung("pytest_wb", nummer="B-2026-7008", eingeloest=deal)

        # Act
        daten = _pruefe(client, auth_headers, "kaeufer@example.com").json()

        # Assert
        assert daten["anrechnungen"] == []

    def test_die_restlaufzeit_steht_dabei(self, client, auth_headers, katalog):
        """„Gültig bis" allein zwingt zum Rechnen; die Zahl steht daneben."""
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7009", gueltig_tage=30)

        # Act
        daten = _pruefe(client, auth_headers, "kaeufer@example.com").json()

        # Assert
        assert daten["anrechnungen"][0]["tage_uebrig"] == 30

    def test_ohne_anmeldung_keine_auskunft(self, client, katalog):
        """Die Route beantwortet, was jemand gekauft hat — das ist eine
        Kundenauskunft und gehört hinter die Anmeldung."""
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7010")

        # Act
        antwort = client.get("/api/shop/credit-check?email=kaeufer@example.com")

        # Assert
        assert antwort.status_code in (401, 403)


# ── Das Einlösen ─────────────────────────────────────────────────────

class TestEinloesen:
    def test_einloesen_vermerkt_deal_und_zeitpunkt(
            self, client, auth_headers, katalog):
        # Arrange
        from database import SessionLocal
        from modelle_buch import BookOrder

        _bestellung("pytest_wb", nummer="B-2026-7020")
        deal = _deal()

        # Act
        antwort = client.post("/api/shop/credit-redeem", headers=auth_headers,
                              json={"order_number": "B-2026-7020",
                                    "deal_id": deal})

        # Assert
        assert antwort.status_code == 200
        db = SessionLocal()
        try:
            e = db.query(BookOrder).filter(
                BookOrder.order_number == "B-2026-7020").first()
            assert e.credit_redeemed_deal_id == deal
            assert e.credit_redeemed_at is not None
        finally:
            db.close()

    def test_zweimal_einloesen_ist_409_und_nennt_den_ersten_deal(
            self, client, auth_headers, katalog):
        """Sonst wird derselbe Betrag mehrfach abgezogen."""
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7021")
        erster, zweiter = _deal("Erster"), _deal("Zweiter")
        client.post("/api/shop/credit-redeem", headers=auth_headers,
                    json={"order_number": "B-2026-7021", "deal_id": erster})

        # Act
        antwort = client.post("/api/shop/credit-redeem", headers=auth_headers,
                              json={"order_number": "B-2026-7021",
                                    "deal_id": zweiter})

        # Assert
        assert antwort.status_code == 409
        assert str(erster) in antwort.json()["detail"]

    def test_eine_abgelaufene_anrechnung_laesst_sich_nicht_einloesen(
            self, client, auth_headers, katalog):
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7022", gueltig_tage=-1)
        deal = _deal()

        # Act
        antwort = client.post("/api/shop/credit-redeem", headers=auth_headers,
                              json={"order_number": "B-2026-7022",
                                    "deal_id": deal})

        # Assert
        assert antwort.status_code == 400

    def test_ein_erfundener_deal_wird_abgelehnt(
            self, client, auth_headers, katalog):
        """Sonst gilt die Anrechnung als verbraucht und zeigt ins Leere."""
        # Arrange
        from database import SessionLocal
        from modelle_buch import BookOrder

        _bestellung("pytest_wb", nummer="B-2026-7023")

        # Act
        antwort = client.post("/api/shop/credit-redeem", headers=auth_headers,
                              json={"order_number": "B-2026-7023",
                                    "deal_id": 999_999})

        # Assert
        assert antwort.status_code == 404
        db = SessionLocal()
        try:
            e = db.query(BookOrder).filter(
                BookOrder.order_number == "B-2026-7023").first()
            assert e.credit_redeemed_deal_id is None
        finally:
            db.close()

    def test_eine_unbekannte_bestellung_ist_404(self, client, auth_headers):
        # Act
        antwort = client.post("/api/shop/credit-redeem", headers=auth_headers,
                              json={"order_number": "B-2026-9999", "deal_id": 1})

        # Assert
        assert antwort.status_code == 404

    def test_ohne_anmeldung_kein_einloesen(self, client, katalog):
        # Arrange
        _bestellung("pytest_wb", nummer="B-2026-7024")

        # Act
        antwort = client.post("/api/shop/credit-redeem",
                              json={"order_number": "B-2026-7024", "deal_id": 1})

        # Assert
        assert antwort.status_code in (401, 403)


# ── Die Ablaufwarnung ────────────────────────────────────────────────

class TestAblaufwarnung:
    def test_genau_dreissig_tage_vor_ablauf_wird_erinnert(
            self, app, katalog, monkeypatch):
        # Arrange
        from services import anrechnung

        _bestellung("pytest_wb", nummer="B-2026-7030", gueltig_tage=30)
        gesendet = []
        monkeypatch.setattr(anrechnung, "_erinnerung_senden",
                            lambda e: gesendet.append(e.order_number) or True)

        # Act
        anzahl = anrechnung.ablaufwarnung()

        # Assert
        assert anzahl == 1
        assert gesendet == ["B-2026-7030"]

    def test_andere_fristen_werden_nicht_erinnert(
            self, app, katalog, monkeypatch):
        """Sonst bekäme derselbe Käufer die Mail an vielen Tagen."""
        # Arrange
        from services import anrechnung

        _bestellung("pytest_wb", nummer="B-2026-7031", gueltig_tage=29)
        _bestellung("pytest_cp", nummer="B-2026-7032", gueltig_tage=31)
        gesendet = []
        monkeypatch.setattr(anrechnung, "_erinnerung_senden",
                            lambda e: gesendet.append(e.order_number) or True)

        # Act
        anrechnung.ablaufwarnung()

        # Assert
        assert gesendet == []

    def test_eine_eingeloeste_anrechnung_wird_nicht_erinnert(
            self, app, katalog, monkeypatch):
        # Arrange
        from services import anrechnung

        deal = _deal()
        _bestellung("pytest_wb", nummer="B-2026-7033", gueltig_tage=30,
                    eingeloest=deal)
        gesendet = []
        monkeypatch.setattr(anrechnung, "_erinnerung_senden",
                            lambda e: gesendet.append(e.order_number) or True)

        # Act
        anrechnung.ablaufwarnung()

        # Assert
        assert gesendet == []

    def test_eine_gescheiterte_mail_haelt_den_lauf_nicht_an(
            self, app, katalog, monkeypatch):
        """Der zweite Käufer soll seine Erinnerung bekommen, auch wenn beim
        ersten Brevo klemmt."""
        # Arrange
        from services import anrechnung

        _bestellung("pytest_wb", nummer="B-2026-7034", gueltig_tage=30,
                    mail="a@example.com")
        _bestellung("pytest_cp", nummer="B-2026-7035", gueltig_tage=30,
                    mail="b@example.com")

        versucht = []

        def mal_kaputt(eintrag):
            versucht.append(eintrag.order_number)
            if eintrag.order_number == "B-2026-7034":
                raise RuntimeError("Brevo antwortet nicht")
            return True

        monkeypatch.setattr(anrechnung, "_erinnerung_senden", mal_kaputt)

        # Act
        anzahl = anrechnung.ablaufwarnung()

        # Assert
        assert sorted(versucht) == ["B-2026-7034", "B-2026-7035"]
        assert anzahl == 1          # nur die gelungene zählt


class TestAngemeldet:
    """Gebaut ist nicht angeschlossen — die Familie L-55, fuenfmal dagewesen."""

    def test_der_taegliche_lauf_ist_im_scheduler_angemeldet(self):
        # Arrange
        import inspect

        from automations import scheduler as s

        quelle = inspect.getsource(s.CompagnonScheduler._register_daily_jobs)

        # Assert
        assert "job_anrechnung_ablaufwarnung" in quelle
        assert 'id="anrechnung_ablaufwarnung"' in quelle

    def test_der_job_ruft_wirklich_den_dienst(self, app, monkeypatch):
        """Gegenprobe: Ein angemeldeter Job, der nichts tut, ist kein Lauf."""
        # Arrange
        from automations.scheduler import job_anrechnung_ablaufwarnung
        from services import anrechnung

        gerufen = []
        monkeypatch.setattr(anrechnung, "ablaufwarnung",
                            lambda *a, **k: gerufen.append(True) or 3)

        # Act
        ergebnis = job_anrechnung_ablaufwarnung()

        # Assert
        assert gerufen == [True]
        assert ergebnis == 3
