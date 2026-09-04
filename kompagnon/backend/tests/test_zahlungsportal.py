# -*- coding: utf-8 -*-
"""Das Zahlungskonto im Kundenportal — Abo, Rechnungen, Zahlungsart.

**Warum kein eigenes Kartenformular.** Der Kunde soll seine Zahlungsart
aendern koennen. Ein eigenes Formular hiesse, Kartendaten durch unseren Server
zu fuehren und damit in den Geltungsbereich von PCI DSS zu geraten. Stripes
Billing-Portal ist dafuer da: Wir erzeugen eine Sitzung und leiten weiter, eine
Kartennummer beruehrt uns nie.

**Was hier gehalten wird**, ist deshalb nicht die Kartenlogik — die gehoert
nicht uns —, sondern die drei Lagen davor: Wo die Kundenkennung herkommt, was
passiert wenn es keine gibt, und dass „kein Konto" und „Dienst nicht
eingerichtet" zwei verschiedene Dinge bleiben. Das eine betrifft den Kunden,
das andere uns.
"""
import pytest

from services import zahlungsportal


@pytest.fixture
def betrieb(app, kunde_user):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == kunde_user.lead_id).first()
        lead.stripe_customer_id = None
        db.commit()
        yield lead.id
        db.refresh(lead)
        lead.stripe_customer_id = None
        db.commit()
    finally:
        db.close()


# ── Woher die Kennung kommt ───────────────────────────────────────────

def test_die_gemerkte_kennung_gewinnt(app, betrieb):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == betrieb).first()
        lead.stripe_customer_id = "cus_gemerkt"
        db.commit()

        assert zahlungsportal.kundenkennung(db, lead) == "cus_gemerkt"
    finally:
        db.close()


def test_ohne_kennung_und_ohne_stripe_gibt_es_keine(app, betrieb, monkeypatch):
    """Ein Betrieb ohne Kauf hat kein Zahlungskonto — das ist kein Fehler."""
    from database import SessionLocal, Lead

    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == betrieb).first()
        with pytest.raises(zahlungsportal.StripeNichtEingerichtet):
            zahlungsportal.portal_sitzung(db, lead, "https://example.de")
    finally:
        db.close()


def test_der_erste_wert_bleibt_stehen(app, betrieb):
    """Stripe legt bei jedem Kauf ohne mitgegebenen Kunden einen neuen an.
    Ihn zu ueberschreiben hiesse, das Portal auf ein Konto zu zeigen, in dem
    nur der letzte Kauf steht."""
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == betrieb).first()
        zahlungsportal.merke_kennung(db, lead, "cus_erster")
        zahlungsportal.merke_kennung(db, lead, "cus_zweiter")

        assert lead.stripe_customer_id == "cus_erster"
    finally:
        db.close()


def test_ein_leerer_wert_ueberschreibt_nichts(app, betrieb):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == betrieb).first()
        zahlungsportal.merke_kennung(db, lead, "cus_echt")
        zahlungsportal.merke_kennung(db, lead, "")

        assert lead.stripe_customer_id == "cus_echt"
    finally:
        db.close()


# ── Der Weg durch das Portal ──────────────────────────────────────────

def test_die_uebersicht_nennt_den_zustand_des_kontos(client, kunde_headers, betrieb,
                                                     monkeypatch):
    """„Kein Konto" und „Dienst nicht eingerichtet" sind zwei Lagen. Ein
    gemeinsames Ja/Nein haette dem Kunden unseren Betriebsfehler angelastet."""
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    antwort = client.get("/api/portal/zahlungen", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["zahlungskonto"] == "dienst_fehlt"
    assert "abos" in d and "rechnungen" in d


def test_ohne_zahlungskonto_gibt_es_keinen_toten_knopf(client, kunde_headers, betrieb,
                                                       monkeypatch):
    """Ein Knopf, der ins Leere fuehrt, ist schlimmer als keiner."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_ungueltig")

    antwort = client.post("/api/portal/zahlungen/verwalten", json={},
                          headers=kunde_headers)

    assert antwort.status_code == 409
    assert "kein Konto" in antwort.json()["detail"]


def test_die_rueckkehradresse_kommt_nicht_aus_dem_aufruf(client, kunde_headers, betrieb,
                                                         monkeypatch):
    """Sonst waere sie eine offene Weiterleitung: Wer den Aufruf faelscht,
    schickt den Kunden nach dem Bezahlen irgendwohin."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_ungueltig")

    antwort = client.post("/api/portal/zahlungen/verwalten",
                          json={"rueckkehr": "https://boese.example/klau"},
                          headers=kunde_headers)

    # 409 statt einer Weiterleitung dorthin — der Wert wird gar nicht gelesen.
    assert antwort.status_code == 409
