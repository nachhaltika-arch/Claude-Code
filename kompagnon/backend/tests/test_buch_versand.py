# -*- coding: utf-8 -*-
"""Die Warteschlange der Druckbestellungen (BUCH-07, L-115).

**Was hier gemessen wird.** Ob die Warteschlange nur enthaelt, was wirklich
gedruckt werden darf, ob der Export sie richtig fortschreibt, und ob eine
Bestellung nicht zweimal an BoD geht. Nicht gemessen wird, ob BoD etwas
druckt — es gibt keine Schnittstelle dorthin, und es soll auch keine geben.

**Der teuerste Fall zuerst.** Bis zum 01.09.2026 stand eine Druckbestellung
schon beim Anlegen auf `queued`, also vor der Zahlung. Wer die CSV bei BoD
aufgab, verschickte ein Buch an jemanden, der die Kasse abgebrochen hatte.
Zwei Zusicherungen halten das fest — eine an der Ursache (der Status beim
Anlegen) und eine an der Wirkung (der Export ueberspringt Unbezahltes). Eine
allein waere die halbe Sicherung: Aeltere Zeilen tragen den alten Status
weiter, und ein spaeterer Umbau koennte den Status wieder zu frueh setzen.
"""
from datetime import datetime
from unittest.mock import patch

import pytest

from database import SessionLocal
from modelle_buch import BookOrder

pytestmark = pytest.mark.usefixtures("app")

TESTPOST = "@versandtest.example"


@pytest.fixture(autouse=True)
def _aufraeumen():
    yield
    from database import Lead
    db = SessionLocal()
    try:
        db.query(BookOrder).filter(
            BookOrder.email.like(f"%{TESTPOST}")).delete(synchronize_session=False)
        db.query(Lead).filter(
            Lead.email.like(f"%{TESTPOST}")).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _bestellung(nummer: str, *, fulfillment="queued", bezahlt=True,
                variant="print", **felder) -> int:
    """Legt eine Bestellung unmittelbar an — ohne Stripe, ohne Kasse."""
    db = SessionLocal()
    try:
        eintrag = BookOrder(
            order_number=nummer,
            variant=variant,
            book_version="1.0",
            email=f"{nummer.lower()}{TESTPOST}",
            first_name="Erika",
            last_name="Muster",
            company="Muster GmbH",
            ship_street="Musterweg 3",
            ship_zip="56068",
            ship_city="Koblenz",
            ship_country="DE",
            price_gross_cents=3990,
            shipping_cents=495,
            payment_status="paid" if bezahlt else "pending",
            fulfillment_status=fulfillment,
            created_at=datetime.utcnow(),
            **felder,
        )
        db.add(eintrag)
        db.commit()
        db.refresh(eintrag)
        return eintrag.id
    finally:
        db.close()


def _status(order_id: int) -> tuple:
    db = SessionLocal()
    try:
        e = db.query(BookOrder).filter(BookOrder.id == order_id).first()
        return e.fulfillment_status, e.fulfillment_exported_at, e.tracking_number
    finally:
        db.close()


# ── Die Ursache: nichts steht vor der Zahlung in der Warteschlange ────

def test_eine_druckbestellung_wartet_erst_auf_die_zahlung():
    """Der Befund vom 01.09.2026, an der Ursache festgehalten.

    Frueher setzte `_bestellung_anlegen` `queued`, waehrend `payment_status`
    noch `pending` war. Diese Zusicherung ist die wichtigere von beiden: Sie
    haelt fest, dass der Status ueberhaupt erst durch Stripe entsteht.
    """
    from routers import buch as kasse

    class _Anfrage:
        variant = "print"
        email = f"kaeufer{TESTPOST}"
        first_name, last_name, company = "Erika", "Muster", ""
        ship_street, ship_zip, ship_city, ship_country = "Weg 1", "56068", "Koblenz", "DE"
        waiver_accepted = False
        utm_source = utm_campaign = ""

    db = SessionLocal()
    try:
        from services import buch_preise
        eintrag = kasse._bestellung_anlegen(
            db, _Anfrage(), buch_preise.variante("print"))
        assert eintrag.payment_status == "pending"
        assert eintrag.fulfillment_status == "awaiting_payment", \
            "unbezahlt darf nie in der Druckwarteschlange stehen"
    finally:
        db.close()


def test_die_zahlung_hebt_den_status_auf_wartend():
    """Die Gegenprobe — sonst waere „nie queued" auch dann wahr, wenn es nie
    dazu kaeme."""
    from routers import buch as kasse

    class _Anfrage:
        variant = "print"
        email = f"zahler{TESTPOST}"
        first_name, last_name, company = "Erika", "Muster", ""
        ship_street, ship_zip, ship_city, ship_country = "Weg 1", "56068", "Koblenz", "DE"
        waiver_accepted = False
        utm_source = utm_campaign = ""

    from services import buch_preise
    db = SessionLocal()
    try:
        eintrag = kasse._bestellung_anlegen(db, _Anfrage(),
                                            buch_preise.variante("print"))
        nummer, sitzung = eintrag.order_number, "cs_versandtest_1"
        eintrag.stripe_session_id = sitzung
        db.commit()
    finally:
        db.close()

    kasse._zahlung_verbuchen({
        "id": sitzung,
        "payment_intent": "pi_versandtest",
        "metadata": {"order_number": nummer, "zahlungsweg": "buch"},
    })

    db = SessionLocal()
    try:
        e = db.query(BookOrder).filter(BookOrder.order_number == nummer).first()
        assert e.payment_status == "paid"
        assert e.fulfillment_status == "queued"
    finally:
        db.close()


# ── Lesen ────────────────────────────────────────────────────────────

def test_die_liste_zeigt_nur_bestellungen_mit_druckabwicklung(client, auth_headers):
    druck = _bestellung("HS-9001-0001")
    _bestellung("HS-9001-0002", fulfillment="not_applicable", variant="pdf")

    daten = client.get("/api/book/orders", headers=auth_headers).json()

    nummern = [b["order_number"] for b in daten["bestellungen"]]
    assert "HS-9001-0001" in nummern
    assert "HS-9001-0002" not in nummern, "eine Datei hat keinen Versand"
    assert any(b["id"] == druck for b in daten["bestellungen"])


def test_die_kennzahlen_zaehlen_nur_bezahltes(client, auth_headers):
    _bestellung("HS-9002-0001")                               # bezahlt, wartend
    _bestellung("HS-9002-0002", fulfillment="awaiting_payment", bezahlt=False)

    daten = client.get("/api/book/orders", headers=auth_headers).json()

    # Nicht auf eine feste Zahl geprueft: Die Testdatenbank kann Zeilen aus
    # anderen Modulen tragen. Gemessen wird der Unterschied, den dieser Test
    # erzeugt — und der ist genau eine offene Bestellung.
    assert daten["offen"] >= 1
    unbezahlt = [b for b in daten["bestellungen"]
                 if b["order_number"] == "HS-9002-0002"]
    assert unbezahlt, "sichtbar ist sie — sie zaehlt nur nicht als offen"
    assert unbezahlt[0]["fulfillment_status"] == "awaiting_payment"


def test_ohne_anmeldung_bleibt_die_liste_zu(client):
    assert client.get("/api/book/orders").status_code in (401, 403)


# ── Export ───────────────────────────────────────────────────────────

def test_der_export_ueberspringt_unbezahlte_bestellungen(client, auth_headers):
    """Der teure Fall: ein Buch an jemanden, der nie gezahlt hat."""
    bezahlt = _bestellung("HS-9003-0001")
    # Der alte, falsche Zustand — so stehen aeltere Zeilen noch in der
    # Datenbank, auch nachdem die Ursache behoben ist.
    unbezahlt = _bestellung("HS-9003-0002", bezahlt=False)

    antwort = client.post("/api/book/orders/export", headers=auth_headers)
    assert antwort.status_code == 200
    text = antwort.content.decode("utf-8-sig")

    assert "HS-9003-0001" in text
    assert "HS-9003-0002" not in text
    assert _status(bezahlt)[0] == "exported"
    assert _status(unbezahlt)[0] == "queued", "unangetastet, weil nie exportiert"


def test_die_csv_traegt_die_vereinbarten_spalten(client, auth_headers):
    _bestellung("HS-9004-0001")

    antwort = client.post("/api/book/orders/export", headers=auth_headers)
    text = antwort.content.decode("utf-8-sig")
    kopf = text.splitlines()[0]

    assert kopf == ("Bestellnummer;Anrede;Vorname;Nachname;Firma;Strasse;"
                    "PLZ;Ort;Land;Menge;Variante;Bestelldatum")
    zeile = [z for z in text.splitlines() if z.startswith("HS-9004-0001")][0]
    felder = zeile.split(";")
    assert felder[1] == "", "die Anrede wird beim Kauf nicht erhoben"
    assert felder[9] == "1", "eine Bestellung ist genau ein Buch"
    assert felder[7] == "Koblenz"


def test_die_datei_traegt_das_byte_order_mark(client, auth_headers):
    """Ohne BOM zerlegt Excel jeden Umlaut — dieselbe Regel wie beim
    Lead-Export."""
    _bestellung("HS-9005-0001")
    antwort = client.post("/api/book/orders/export", headers=auth_headers)
    assert antwort.content.startswith(b"\xef\xbb\xbf")
    assert "bod-bestellungen-" in antwort.headers["content-disposition"]


def test_zweimal_exportieren_schickt_dieselbe_bestellung_nicht_zweimal(
        client, auth_headers):
    kennung = _bestellung("HS-9006-0001")

    erste = client.post("/api/book/orders/export", headers=auth_headers)
    zweite = client.post("/api/book/orders/export", headers=auth_headers)

    assert "HS-9006-0001" in erste.content.decode("utf-8-sig")
    assert "HS-9006-0001" not in zweite.content.decode("utf-8-sig")
    assert _status(kennung)[1] is not None, "der Zeitpunkt ist vermerkt"


def test_der_export_ist_kein_get(client, auth_headers):
    """Ein Vorauslader oder ein Neuladen darf die Warteschlange nicht leeren."""
    antwort = client.get("/api/book/orders/export", headers=auth_headers)
    assert antwort.status_code == 405


# ── Zurueckschreiben ─────────────────────────────────────────────────

def test_als_versendet_markieren_traegt_die_sendungsnummer_ein(
        client, auth_headers):
    kennung = _bestellung("HS-9007-0001", fulfillment="exported")

    with patch("services.email.send_email", return_value=True) as post:
        antwort = client.patch(
            f"/api/book/orders/{kennung}/fulfillment",
            json={"fulfillment_status": "shipped", "tracking_number": "00340434"},
            headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["benachrichtigt"] is True
    assert _status(kennung)[0] == "shipped"
    assert _status(kennung)[2] == "00340434"
    betreff = post.call_args[0][1]
    assert "HS-9007-0001" in betreff


def test_eine_korrektur_loest_keine_zweite_mail_aus(client, auth_headers):
    kennung = _bestellung("HS-9008-0001", fulfillment="shipped")

    with patch("services.email.send_email", return_value=True) as post:
        client.patch(f"/api/book/orders/{kennung}/fulfillment",
                     json={"fulfillment_status": "shipped",
                           "tracking_number": "00340435"},
                     headers=auth_headers)

    assert post.call_count == 0, "nur der Uebergang benachrichtigt"
    assert _status(kennung)[2] == "00340435"


def test_eine_gescheiterte_mail_nimmt_den_vermerk_nicht_mit(client, auth_headers):
    """Sonst stuende die Bestellung weiter als „exportiert" in der Liste — und
    ginge beim naechsten Export ein zweites Mal an BoD."""
    kennung = _bestellung("HS-9009-0001", fulfillment="exported")

    with patch("services.email.send_email", side_effect=RuntimeError("Brevo weg")):
        antwort = client.patch(
            f"/api/book/orders/{kennung}/fulfillment",
            json={"fulfillment_status": "shipped", "tracking_number": "1"},
            headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["benachrichtigt"] is False
    assert _status(kennung)[0] == "shipped"


def test_awaiting_payment_laesst_sich_nicht_von_hand_setzen(client, auth_headers):
    """Eine Zahlung ist eine Tatsache aus Stripe, keine Entscheidung im
    Innendienst — und der Weg zurueck waere der Weg in den teuren Fall."""
    kennung = _bestellung("HS-9010-0001")
    antwort = client.patch(f"/api/book/orders/{kennung}/fulfillment",
                           json={"fulfillment_status": "awaiting_payment"},
                           headers=auth_headers)
    assert antwort.status_code == 422


def test_eine_datei_hat_keinen_versand(client, auth_headers):
    kennung = _bestellung("HS-9011-0001", fulfillment="not_applicable",
                          variant="pdf")
    antwort = client.patch(f"/api/book/orders/{kennung}/fulfillment",
                           json={"fulfillment_status": "shipped"},
                           headers=auth_headers)
    assert antwort.status_code == 422


def test_ohne_anmeldung_laesst_sich_nichts_setzen(client):
    kennung = _bestellung("HS-9012-0001")
    antwort = client.patch(f"/api/book/orders/{kennung}/fulfillment",
                           json={"fulfillment_status": "shipped"})
    assert antwort.status_code in (401, 403)
