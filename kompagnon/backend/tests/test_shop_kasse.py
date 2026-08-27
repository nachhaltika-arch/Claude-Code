# -*- coding: utf-8 -*-
"""Der Bezahlvorgang für digitale Produkte (L-100, ORDERS_03).

**Die zwei Zusicherungen, an denen wirklich etwas hängt:**

1. **Der Preis kommt nie aus der Anfrage.** ORDERS_03 nennt das
   sicherheitskritisch, und zu Recht: Wird der Betrag übernommen, kauft jeder
   das Workbook für einen Cent.
2. **Ein Verbraucher ohne Widerrufsverzicht wird abgelehnt.** § 356 Abs. 5
   BGB — ohne Verzicht darf nicht sofort ausgeliefert werden, und ohne
   Belehrung läuft die Frist **nie** ab. Die vollständige Umsetzung kommt in
   ORDERS_05; die Sperre steht schon jetzt, damit sie nicht vergessen wird.

**Ein Entwurf ist kein Angebot.** Die drei digitalen Produkte stehen bis
ORDERS_05 auf `draft`. Auch ein von Hand zusammengebauter Aufruf muss an
ihnen scheitern — ein Riegel, den nur die Oberfläche kennt, ist keiner.
"""
import pytest


@pytest.fixture()
def verkaufbares_produkt(app):
    """Ein `live` gestelltes Testprodukt — und danach wieder weg.

    Die echten drei stehen auf `draft`; gegen sie liesse sich der Erfolgsfall
    nicht pruefen, und sie dafuer live zu stellen waere genau der Riegel, den
    dieser Test schuetzen soll.
    """
    from sqlalchemy import text

    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO products (slug, name, short_desc, price_brutto,
                                  price_netto, tax_rate, payment_type, status,
                                  is_creditable, credit_months, delivery_type)
            VALUES ('pytest_probeprodukt', 'Pytest Probeprodukt', 'Probe',
                    100.00, 93.46, 7, 'once', 'live', true, 6, 'download')
            ON CONFLICT (slug) DO NOTHING"""))
        db.commit()
    finally:
        db.close()

    yield "pytest_probeprodukt"

    db = SessionLocal()
    try:
        from modelle_buch import BookOrder

        db.query(BookOrder).filter(
            BookOrder.product_slug == "pytest_probeprodukt").delete()
        db.execute(text("DELETE FROM products WHERE slug='pytest_probeprodukt'"))
        db.commit()
    finally:
        db.close()


def _anfrage(**abweichend):
    grund = {
        "product_code": "pytest_probeprodukt",
        "buyer_email": "kaeufer@example.com",
        "buyer_name": "Erika Musterfrau",
        "buyer_address": "Teststr. 1, 56068 Koblenz",
        "is_business": True,
        "terms_accepted": True,
        "withdrawal_waived": True,
    }
    grund.update(abweichend)
    return grund


# ── Der Riegel ────────────────────────────────────────────────────────

def test_verbraucher_ohne_verzicht_wird_abgelehnt(client, verkaufbares_produkt):
    antwort = client.post("/api/shop/checkout", json=_anfrage(
        is_business=False, withdrawal_waived=False))

    assert antwort.status_code == 400, antwort.text[:300]
    text = antwort.json()["detail"].lower()
    assert "widerruf" in text, text


def test_verbraucher_mit_verzicht_kommt_durch(client, verkaufbares_produkt):
    """Die Gegenprobe. Ohne sie waere der Riegel auch dann „gruen", wenn er
    **jeden** Verbraucher abwiese."""
    antwort = client.post("/api/shop/checkout", json=_anfrage(
        is_business=False, withdrawal_waived=True))

    # 503 heisst: bis zur Stripe-Pruefung gekommen — der Riegel hat ihn
    # durchgelassen. Ohne Schluessel geht es nicht weiter, und das ist hier
    # der erwartete Zustand.
    assert antwort.status_code != 400, antwort.text[:300]


def test_ein_geschaeftskunde_braucht_keinen_verzicht(client, verkaufbares_produkt):
    """§ 355 BGB gilt Verbrauchern, nicht Unternehmern."""
    antwort = client.post("/api/shop/checkout", json=_anfrage(
        is_business=True, withdrawal_waived=False))

    assert antwort.status_code != 400, antwort.text[:300]


# ── Ein Entwurf ist kein Angebot ──────────────────────────────────────
#
# **`app` steht hier nicht aus Gewohnheit.** Ohne die Fixture laufen die
# Migrationen nicht, und `products` traegt dann nur die Spalten, die
# `create_all` anlegt — `status` und `short_desc` fehlen. Der Aufruf
# scheitert dann an der Datenbank statt am Riegel, und der Test saehe rot
# aus, ohne etwas ueber den Riegel zu sagen. Genau die Falle aus
# `docs`: zwei Wege fuer Tabellen, im Test lief nur einer.

@pytest.mark.parametrize("slug", ["workbook_homepage_standard", "check_plus",
                                  "buch_homepage_standard"])
def test_die_entwuerfe_sind_nicht_bestellbar(app, client, slug):
    antwort = client.post("/api/shop/checkout", json=_anfrage(product_code=slug))

    assert antwort.status_code == 404, antwort.text[:300]


def test_ein_erfundenes_produkt_gibt_404(app, client):
    antwort = client.post("/api/shop/checkout",
                          json=_anfrage(product_code="gibtesnicht"))

    assert antwort.status_code == 404


# ── Der Preis kommt aus dem Katalog ───────────────────────────────────

def test_der_betrag_aus_der_anfrage_wird_ignoriert(app, verkaufbares_produkt):
    """**Sicherheitskritisch.** Am Dienst gemessen, nicht am Endpunkt: Ohne
    Stripe-Schluessel kommt der Aufruf nicht bis zur Anlage, also wird die
    Regel dort geprueft, wo sie steht."""
    from sqlalchemy import text

    from database import SessionLocal
    from services import bestellung as best

    db = SessionLocal()
    try:
        produkt = best.produkt_holen(db, verkaufbares_produkt)
        eintrag = best.anlegen(db, _anfrage(
            price_brutto=1, amount_gross=1, price_gross_cents=1), produkt)
        nummer = eintrag.order_number
        assert eintrag.price_gross_cents == 10000, (
            f"{eintrag.price_gross_cents} Cent statt 10000 — der Preis kam "
            "aus der Anfrage")

        # Und die Bestellnummer traegt das vereinbarte Format.
        assert nummer.startswith("B-"), nummer
        assert len(nummer.split("-")) == 3, nummer

        # Anrechnung: sechs Monate, aus dem Katalog.
        assert eintrag.credit_valid_until is not None
        assert eintrag.is_business is True
        assert eintrag.waiver_accepted_at is not None
        assert eintrag.payment_status == "created"

        db.execute(text("DELETE FROM book_orders WHERE order_number = :n"),
                   {"n": nummer})
        db.commit()
    finally:
        db.close()


@pytest.mark.parametrize("produkt,erwartet", [
    ({"is_creditable": False, "credit_months": 6}, None),
    ({"is_creditable": True, "credit_months": 0}, None),
    ({"is_creditable": True, "credit_months": None}, None),
])
def test_ohne_anrechnung_bleibt_die_frist_leer(produkt, erwartet):
    """`None` ist eine Aussage. Eine Frist, die niemand zugesagt hat, waere
    eine Zusage."""
    from services.bestellung import frist_bis

    assert frist_bis(produkt) is erwartet


def test_sechs_monate_sind_sechs_monate():
    """Die Gegenprobe — sonst waere der Test oben auch gruen, wenn `frist_bis`
    **immer** `None` zurueckgaebe."""
    from datetime import date

    from services.bestellung import frist_bis

    gerechnet = frist_bis({"is_creditable": True, "credit_months": 6},
                          heute=date(2026, 8, 27))

    assert gerechnet == date(2027, 2, 27)


def test_ein_tag_der_im_zielmonat_fehlt_zieht_zurueck():
    """31. August plus sechs Monate waere der 31. Februar.

    Ohne diesen Rueckzug wuerde die Bestellung mit einem `ValueError`
    scheitern — nach der Zahlung, im Zahlungspfad.
    """
    from datetime import date

    from services.bestellung import frist_bis

    gerechnet = frist_bis({"is_creditable": True, "credit_months": 6},
                          heute=date(2026, 8, 31))

    assert gerechnet == date(2027, 2, 28)


# ── Die Eingabepruefung ───────────────────────────────────────────────

@pytest.mark.parametrize("feld,wert", [
    ("buyer_email", "keine-adresse"),
    ("buyer_email", ""),
    ("buyer_name", "  "),
    ("buyer_address", ""),
])
def test_unvollstaendige_angaben_werden_benannt(client, verkaufbares_produkt,
                                                feld, wert):
    antwort = client.post("/api/shop/checkout", json=_anfrage(**{feld: wert}))

    assert antwort.status_code == 400, f"{feld}={wert!r} -> {antwort.status_code}"


def test_ohne_agb_kein_kauf(client, verkaufbares_produkt):
    antwort = client.post("/api/shop/checkout",
                          json=_anfrage(terms_accepted=False))

    assert antwort.status_code == 400
    assert "agb" in antwort.json()["detail"].lower()
