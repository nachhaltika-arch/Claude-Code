# -*- coding: utf-8 -*-
"""
Der Verkauf des Buchs: Kasse, Zahlungsmeldung, Auskunft (BUCH-04, BUCH-05).

Geprüft wird das, was Geld und Recht berührt — nicht, ob Stripe funktioniert.
Der Aufruf an Stripe wird ersetzt; was zählt, ist, **was wir ihm übergeben**
und was wir aus seiner Antwort machen.
"""
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database import SessionLocal
from main import app
from modelle_buch import BookOrder
from routers import buch as buch_router
from services import buch_preise

#: **Das Schema kommt aus `conftest`, nicht aus diesem Modul.** `book_orders`
#: ist neu; eine Testdatenbank von gestern kennt sie nicht. Die Fixture `app`
#: baut das Schema einmal je Lauf neu auf — ohne sie wäre dieser Test lokal
#: grün (weil die Entwicklungsdatenbank die Tabelle aus einem echten Start
#: trägt) und in der CI rot. Genau dieser Unterschied hat das Projekt am
#: 23.08.2026 schon einmal gekostet.
pytestmark = pytest.mark.usefixtures("app")

client = TestClient(app)


@pytest.fixture(autouse=True)
def _aufraeumen():
    yield
    # **Reihenfolge zählt.** Die Bestellung zeigt auf den Lead; wer den Lead
    # zuerst löscht, bekommt einen Fremdschlüsselfehler — dieselbe Klasse wie
    # L-56, wo ein Betrieb mit Kundenzugang nicht löschbar war.
    from database import Lead
    db = SessionLocal()
    try:
        db.query(BookOrder).filter(
            BookOrder.email.like("%@buchtest.example")).delete(
                synchronize_session=False)
        db.query(Lead).filter(
            Lead.email.like("%@buchtest.example")).delete(
                synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _bestellung(**felder) -> dict:
    grund = {
        "variant": "pdf",
        "email": "kaeufer@buchtest.example",
        "first_name": "Erika",
        "last_name": "Muster",
        "waiver_accepted": True,
    }
    grund.update(felder)
    return grund


class _Sitzung:
    id = "cs_test_123"
    url = "https://checkout.stripe.com/c/pay/cs_test_123"


# ── Was ohne Zustimmung nicht verkauft wird ──────────────────────────

def test_pdf_ohne_verzicht_auf_widerruf_wird_abgelehnt():
    """§ 356 Abs. 5 BGB — ohne Zustimmung bleibt das Widerrufsrecht bestehen.

    Bei einer Datei, die der Käufer sofort bekommt, hieße das: vierzehn Tage
    Rückgaberecht auf etwas, das er längst hat.
    """
    antwort = client.post("/api/book/checkout",
                          json=_bestellung(waiver_accepted=False))
    assert antwort.status_code == 422
    assert "sofortigen Beginn" in antwort.text


def test_gedruckte_ausgabe_ohne_anschrift_wird_abgelehnt():
    antwort = client.post("/api/book/checkout",
                          json=_bestellung(variant="print", waiver_accepted=False))
    assert antwort.status_code == 422
    for pflicht in ("Straße", "Postleitzahl", "Ort"):
        assert pflicht in antwort.text


def test_unbekannte_ausgabe_wird_abgelehnt():
    antwort = client.post("/api/book/checkout", json=_bestellung(variant="hoerbuch"))
    assert antwort.status_code == 422


def test_ungueltige_adresse_wird_abgelehnt():
    antwort = client.post("/api/book/checkout", json=_bestellung(email="keine-adresse"))
    assert antwort.status_code == 422


# ── Was an Stripe übergeben wird ─────────────────────────────────────

def test_die_kasse_uebergibt_preis_und_steuersatz_aus_einer_quelle():
    with patch.object(buch_router, "FRONTEND_BOOK_URL", "https://buch.example"), \
         patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test"}), \
         patch("stripe.checkout.Session.create", return_value=_Sitzung()) as ruf:
        antwort = client.post("/api/book/checkout",
                              json=_bestellung(variant="bundle",
                                               ship_street="Musterweg 1",
                                               ship_zip="44787", ship_city="Bochum"))

    assert antwort.status_code == 200, antwort.text
    argumente = ruf.call_args.kwargs
    positionen = argumente["line_items"]
    variante = buch_preise.VARIANTEN["bundle"]
    assert positionen[0]["price_data"]["unit_amount"] == variante["brutto_cents"]
    assert positionen[1]["price_data"]["unit_amount"] == variante["versand_cents"]
    assert argumente["metadata"]["order_number"] == antwort.json()["order_number"]
    assert argumente["metadata"]["book_version"] == buch_preise.BUCH_FASSUNG


def test_die_bestellung_steht_vor_dem_bezahlen_in_der_datenbank():
    """Sonst geht der Kauf verloren, sobald der Webhook feuert."""
    with patch.object(buch_router, "FRONTEND_BOOK_URL", "https://buch.example"), \
         patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test"}), \
         patch("stripe.checkout.Session.create", return_value=_Sitzung()):
        antwort = client.post("/api/book/checkout", json=_bestellung())

    nummer = antwort.json()["order_number"]
    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == nummer).first()
        assert eintrag is not None
        assert eintrag.payment_status == "pending"
        assert eintrag.stripe_session_id == _Sitzung.id
        assert eintrag.tax_rate == pytest.approx(7.00)
        assert eintrag.waiver_accepted_at is not None
        assert eintrag.book_version == buch_preise.BUCH_FASSUNG
    finally:
        db.close()


def test_die_bestellnummer_zaehlt_hoch():
    with patch.object(buch_router, "FRONTEND_BOOK_URL", "https://buch.example"), \
         patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test"}), \
         patch("stripe.checkout.Session.create", return_value=_Sitzung()):
        erste = client.post("/api/book/checkout", json=_bestellung()).json()
        _Sitzung.id = "cs_test_456"
        zweite = client.post("/api/book/checkout", json=_bestellung()).json()

    assert erste["order_number"].startswith(f"HS-{datetime.utcnow().year}-")
    assert zweite["order_number"] > erste["order_number"]
    _Sitzung.id = "cs_test_123"


# ── Die Zahlungsmeldung ──────────────────────────────────────────────

def _angelegt(**felder) -> str:
    db = SessionLocal()
    try:
        eintrag = BookOrder(
            order_number=f"HS-2026-9{db.query(BookOrder).count() % 900:03d}",
            variant=felder.get("variant", "pdf"),
            book_version="2026.2",
            email="kaeufer@buchtest.example",
            price_gross_cents=3900, tax_rate=7, shipping_cents=0,
            stripe_session_id=felder.get("sitzung", "cs_hook_1"),
            payment_status=felder.get("status", "pending"),
            waiver_accepted=True,
        )
        db.add(eintrag)
        db.commit()
        return eintrag.order_number
    finally:
        db.close()


def test_bezahlt_setzt_abruf_und_verknuepft_den_kaeufer():
    """Der Käufer muss in der Pipeline auftauchen — sonst ist er weg."""
    from database import Lead

    nummer = _angelegt(sitzung="cs_hook_2")
    buch_router._zahlung_verbuchen({"id": "cs_hook_2", "payment_intent": "pi_1"})

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(
            BookOrder.order_number == nummer).first()
        assert eintrag.payment_status == "paid"
        assert eintrag.download_token, "ohne Token gibt es keinen Abruf"
        assert eintrag.download_expires_at > datetime.utcnow()
        assert eintrag.lead_id, "der Käufer ist in keiner Pipeline gelandet"
        lead = db.query(Lead).filter(Lead.id == eintrag.lead_id).first()
        assert lead.lead_source == "buch"
    finally:
        db.close()


def test_zweimal_dieselbe_meldung_aendert_nichts():
    """Stripe sendet mehrfach. Ein zweiter Lauf darf kein zweites Mal wirken."""
    nummer = _angelegt(sitzung="cs_hook_3")
    buch_router._zahlung_verbuchen({"id": "cs_hook_3", "payment_intent": "pi_2"})

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(BookOrder.order_number == nummer).first()
        erstes_token, lead_id = eintrag.download_token, eintrag.lead_id
    finally:
        db.close()

    buch_router._zahlung_verbuchen({"id": "cs_hook_3", "payment_intent": "pi_2"})

    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(BookOrder.order_number == nummer).first()
        assert eintrag.download_token == erstes_token
        assert eintrag.lead_id == lead_id
    finally:
        db.close()


def test_gedruckte_ausgabe_geht_in_die_warteschlange():
    nummer = _angelegt(variant="print", sitzung="cs_hook_4")
    buch_router._zahlung_verbuchen({"id": "cs_hook_4", "payment_intent": "pi_3"})
    db = SessionLocal()
    try:
        eintrag = db.query(BookOrder).filter(BookOrder.order_number == nummer).first()
        assert eintrag.fulfillment_status == "queued"
        assert not eintrag.download_token, "die gedruckte Ausgabe hat keinen Abruf"
    finally:
        db.close()


def test_ohne_gueltige_signatur_wird_nichts_verbucht():
    antwort = client.post("/api/book/webhook", content=b"{}",
                          headers={"stripe-signature": "unsinn"})
    assert antwort.status_code == 400


# ── Die Auskunft für die Danke-Seite ─────────────────────────────────

def test_die_auskunft_gibt_keine_adressdaten_preis():
    """Diese Route ist öffentlich — wer eine Nummer rät, darf nichts erfahren."""
    nummer = _angelegt(sitzung="cs_hook_5")
    antwort = client.get(f"/api/book/order/{nummer}")
    assert antwort.status_code == 200
    daten = antwort.json()
    assert set(daten) == {"order_number", "variant", "payment_status", "email_masked"}
    assert "kaeufer@buchtest.example" not in antwort.text
    assert daten["email_masked"].endswith("@buchtest.example")


def test_unbekannte_bestellung_gibt_404():
    assert client.get("/api/book/order/HS-1999-0001").status_code == 404


def test_die_varianten_kommen_aus_einer_quelle():
    daten = client.get("/api/book/varianten").json()
    assert daten["tax_rate"] == 7.0
    assert set(daten["variants"]) == set(buch_preise.VARIANTEN)
    for schluessel, werte in daten["variants"].items():
        quelle = buch_preise.VARIANTEN[schluessel]
        assert werte["total_cents"] == quelle["brutto_cents"] + quelle["versand_cents"]
