# -*- coding: utf-8 -*-
"""Was ein Bestandskunde dazubuchen kann (Entwurf `kundenkonto-neu`).

**Zwei Angebote, und beide sind gepruefte Produkte:** der Wechsel auf Pflege
Pro und das GEO/GAIO-Add-on. **Check PLUS und Workbook stehen bewusst nicht
dabei** — beide brauchen einen Bestellweg, den es nicht gibt (L-100), und das
Workbook ist nicht geschrieben. Etwas anzubieten, das man nicht liefern kann,
ist teurer als es nicht anzubieten.

**Die Buchung ist eine verbindliche Erklaerung, keine Automatik.** Ein Wechsel
auf Pflege Pro heisst: Lastschrift ueber 177,31 € im Monat. Den Vertrag zu
wechseln **und** das Stripe-Abo umzustellen, waere zwei Eingriffe ins Geld auf
einen Klick. Was hier entsteht, ist die Erklaerung mit Zeitpunkt und Wortlaut;
umgesetzt wird sie vom Innendienst. Im Streit ist das der Unterschied zwischen
einem Nachweis und einer Behauptung.

**Wer nur ansehen darf, bucht nicht.** Das ist eine Handlung am Vertrag —
dieselbe Grenze wie beim Freigeben (L-160 Rang 4).
"""
import pytest


@pytest.fixture
def basic_kunde(app, kunde_user):
    from datetime import datetime

    from database import AboVertrag, SessionLocal
    from services import abo_vertrag
    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.execute(text("DELETE FROM buchungen WHERE lead_id = :l"),
                   {"l": kunde_user.lead_id})
        db.commit()
        abo_vertrag.anlegen(db, lead_id=kunde_user.lead_id, produkt="ABO-BAS",
                            start_monat=datetime.utcnow().strftime("%Y-%m"),
                            wer="test@kompagnon.eu")
    finally:
        db.close()
    yield kunde_user.lead_id
    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.execute(text("DELETE FROM buchungen WHERE lead_id = :l"),
                   {"l": kunde_user.lead_id})
        db.commit()
    finally:
        db.close()


# ── Der Katalog ───────────────────────────────────────────────────────

def test_jedes_angebot_traegt_preis_zahlung_laufzeit_und_rechtstext():
    """**Ohne diese vier kauft niemand.** Ein Preis ohne Zahlungsbedingung
    laesst offen, wann abgebucht wird; eine Laufzeit ohne Rechtstext laesst
    offen, worauf man sich einlaesst."""
    from services import dazubuchen as db

    assert db.ANGEBOTE
    for a in db.ANGEBOTE.values():
        assert a.netto_cent > 0 and a.brutto_cent > a.netto_cent
        assert len(a.zahlung) > 20
        assert len(a.laufzeit) > 15
        assert len(a.rechtstext) > 60, f"{a.kennung} erklärt zu wenig"


def test_die_abo_preise_kommen_aus_der_abrechnung_nicht_von_hand():
    """Zwei Fassungen desselben Preises laufen auseinander — und die eine
    steht dann auf dem Bildschirm, die andere auf der Rechnung."""
    from services import abo_stunden, dazubuchen

    pro = dazubuchen.ANGEBOTE["ABO-PRO"]

    assert pro.netto_cent == abo_stunden.preis_netto_cent("ABO-PRO")
    assert pro.brutto_cent == abo_stunden.preis_brutto_cent("ABO-PRO")


def test_check_plus_und_workbook_stehen_nicht_drin():
    """Beide brauchen einen Bestellweg, den es nicht gibt (L-100); das
    Workbook ist zudem nicht geschrieben."""
    from services import dazubuchen

    kennungen = set(dazubuchen.ANGEBOTE)
    assert not {k for k in kennungen if "CHECK" in k.upper() or "WORK" in k.upper()}


# ── Der Weg durch das Portal ──────────────────────────────────────────

def test_ein_basic_kunde_bekommt_den_wechsel_angeboten(client, kunde_headers,
                                                       basic_kunde):
    d = client.get("/api/portal/dazubuchen", headers=kunde_headers).json()

    kennungen = {a["kennung"] for a in d["angebote"]}
    assert "ABO-PRO" in kennungen
    assert "GEO-01" in kennungen
    pro = next(a for a in d["angebote"] if a["kennung"] == "ABO-PRO")
    assert pro["buchbar"] is True
    assert pro["gebucht"] is False


def test_wer_pflege_pro_hat_bekommt_es_nicht_noch_einmal(client, kunde_headers,
                                                         kunde_user):
    """Sonst stuende auf dem Bildschirm ein Wechsel zu dem, was man schon hat."""
    from datetime import datetime

    from database import AboVertrag, SessionLocal
    from services import abo_vertrag

    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.commit()
        abo_vertrag.anlegen(db, lead_id=kunde_user.lead_id, produkt="ABO-PRO",
                            start_monat=datetime.utcnow().strftime("%Y-%m"),
                            wer="test@kompagnon.eu")
    finally:
        db.close()

    d = client.get("/api/portal/dazubuchen", headers=kunde_headers).json()
    pro = next(a for a in d["angebote"] if a["kennung"] == "ABO-PRO")
    assert pro["buchbar"] is False
    assert pro["grund"], "warum es nicht buchbar ist, gehört dazu"

    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.commit()
    finally:
        db.close()


def test_eine_buchung_braucht_die_bestaetigung_im_wortlaut(client, kunde_headers,
                                                           basic_kunde):
    """**Ein Klick ist zu wenig fuer eine Lastschrift.** Der Kunde bestaetigt
    ausdruecklich, dass er den Rechtstext gelesen hat."""
    ohne = client.post("/api/portal/dazubuchen/ABO-PRO", headers=kunde_headers,
                       json={"verstanden": False})

    assert ohne.status_code == 400


def test_eine_buchung_wird_festgehalten_und_nicht_ausgefuehrt(
        client, kunde_headers, basic_kunde):
    """**Der Kern.** Vertrag wechseln **und** Stripe umstellen waere zwei
    Eingriffe ins Geld auf einen Klick. Was entsteht, ist die Erklaerung."""
    from database import AboVertrag, SessionLocal

    antwort = client.post("/api/portal/dazubuchen/ABO-PRO", headers=kunde_headers,
                          json={"verstanden": True})

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["gebucht_am"] and d["ab_monat"]
    assert d["danach"], "der Kunde muss lesen, was jetzt geschieht"

    db = SessionLocal()
    try:
        # Der laufende Vertrag ist unveraendert — die Umsetzung macht der
        # Innendienst, nicht der Klick.
        vertraege = (db.query(AboVertrag)
                     .filter(AboVertrag.lead_id == basic_kunde).all())
        assert {v.produkt for v in vertraege} == {"ABO-BAS"}
    finally:
        db.close()


def test_der_wortlaut_wird_mitgeschrieben(client, kunde_headers, basic_kunde):
    """**Wozu genau er zugestimmt hat.** Aendern wir den Rechtstext spaeter,
    belegt die Buchung sonst nur, dass jemand irgendwann geklickt hat —
    dieselbe Ueberlegung wie bei der AGB-Fassung (ORDERS_05)."""
    from sqlalchemy import text

    from database import SessionLocal

    client.post("/api/portal/dazubuchen/GEO-01", headers=kunde_headers,
                json={"verstanden": True})

    db = SessionLocal()
    try:
        zeile = db.execute(text(
            "SELECT rechtstext, preis_brutto_cent FROM buchungen "
            "WHERE lead_id = :l AND kennung = 'GEO-01'"),
            {"l": basic_kunde}).fetchone()
        assert zeile and len(zeile[0]) > 60
        assert zeile[1] > 0, "der Preis von heute gehört zur Erklärung"
    finally:
        db.close()


def test_ein_mitleser_bucht_nicht(client, app, kunde_user, basic_kunde):
    """Eine Handlung am Vertrag — dieselbe Grenze wie beim Freigeben."""
    from auth import hash_password
    from database import SessionLocal, User
    from services.kundenzugang import ANSEHEN

    mail, wort = "bucht-nicht@example.org", "Mitleser!2026"
    db = SessionLocal()
    try:
        alt = db.query(User).filter(User.email == mail).first()
        if alt:
            db.delete(alt); db.commit()
        db.add(User(email=mail, role="kunde", password_hash=hash_password(wort),
                    lead_id=kunde_user.lead_id, is_active=True, is_verified=True,
                    kunde_recht=ANSEHEN))
        db.commit()
    finally:
        db.close()

    anmeldung = client.post("/api/auth/login", json={"email": mail, "password": wort})
    kopf = {"Authorization": f"Bearer {anmeldung.json()['access_token']}"}

    antwort = client.post("/api/portal/dazubuchen/ABO-PRO", headers=kopf,
                          json={"verstanden": True})
    assert antwort.status_code == 403

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == mail).first()
        if u:
            db.delete(u); db.commit()
    finally:
        db.close()
