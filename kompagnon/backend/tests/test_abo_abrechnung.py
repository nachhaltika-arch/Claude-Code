# -*- coding: utf-8 -*-
"""Die monatliche Abrechnung der Pflege-Abos (L-101, letzter Teil).

**Die Entscheidung: per Rechnung, nicht per Abbuchung** (David, 01.09.2026).
Damit ist der Eintrag beantwortet — Stripe kann Abonnements, wir nutzen sie
nicht.

**Der Lauf stellt keine Rechnung aus**, und die Tests halten das fest. Eine
Rechnungsnummer ist fortlaufend und lässt sich nicht still zurücknehmen;
`services/rechnung.py` sagt es selbst: „Eine zweite Nummer für denselben
Vorgang reisst eine Lücke in den Kreis." Was der Lauf tut, ist die Aufstellung
— wer, welches Abo, welcher Monat, welcher Betrag.

**Die Steuer ist 19 %, nicht 7 %.** Das Buch ist ermässigt, eine Dienstleistung
nicht — und 12 Prozentpunkte auf jede Monatsrechnung fallen in einer Summe
nicht auf, sondern erst bei der Umsatzsteuervoranmeldung.
"""
from datetime import datetime

import pytest

from services import abo_abrechnung, abo_stunden, abo_vertrag

BETRIEB_NAME = "Malerei Abrechnung-Nur-Im-Test"

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture()
def db(app):
    from database import SessionLocal
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture()
def betrieb(db):
    from database import Benachrichtigung, Lead, TimeTracking
    from modelle_abo import AboVertrag

    lead = Lead(company_name=BETRIEB_NAME)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    kennung = lead.id
    try:
        yield kennung
    finally:
        db.query(Benachrichtigung).filter(
            Benachrichtigung.lead_id == kennung).delete()
        db.query(TimeTracking).filter(TimeTracking.lead_id == kennung).delete()
        db.query(AboVertrag).filter(AboVertrag.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()


@pytest.fixture(autouse=True)
def _meldungen_aufraeumen(db):
    from database import Benachrichtigung
    yield
    db.query(Benachrichtigung).filter(
        Benachrichtigung.titel.like("Abrechnung %")).delete()
    db.commit()


def _meiner(posten, kennung):
    return [p for p in posten if p["lead_id"] == kennung]


# ── Die Aufstellung ──────────────────────────────────────────────────

def test_ein_laufendes_abo_steht_mit_brutto_und_steuer_da(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")

    posten = _meiner(abo_abrechnung.offene_posten(db, "2026-09"), betrieb)

    assert len(posten) == 1
    p = posten[0]
    assert p["produkt"] == "ABO-PRO"
    assert p["netto_cent"] == 14900
    assert p["steuersatz"] == 19.0
    assert p["steuer_cent"] == 2831        # 149,00 € × 19 %
    assert p["brutto_cent"] == 17731
    assert p["monat"] == "2026-09"


def test_basic_kostet_neunundsiebzig(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-08")

    p = _meiner(abo_abrechnung.offene_posten(db, "2026-09"), betrieb)[0]

    assert p["netto_cent"] == 7900
    assert p["brutto_cent"] == 7900 + 1501


def test_der_preis_haengt_nicht_an_den_geleisteten_stunden(db, betrieb):
    """Ein Abo ist eine Pauschale. Mehrarbeit wird gesondert beauftragt —
    sie darf den Monatspreis nicht still erhöhen."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")
    abo_stunden.eintragen(db, lead_id=betrieb, stunden=9.0, wer="Test",
                          monat="2026-09")

    p = _meiner(abo_abrechnung.offene_posten(db, "2026-09"), betrieb)[0]

    assert p["netto_cent"] == 14900
    assert p["verbraucht_stunden"] == 9.0
    assert p["ueberzogen"] is True, "sichtbar muss es trotzdem sein"


def test_ohne_vertrag_steht_nichts_an(db, betrieb):
    assert _meiner(abo_abrechnung.offene_posten(db, "2026-09"), betrieb) == []


def test_ein_beendetes_abo_wird_nicht_weiter_berechnet(db, betrieb):
    """**Der teuerste Fehler waere dieser.** Eine Rechnung an einen
    gekündigten Kunden ist nicht nur falsch, sie ist peinlich."""
    vertrag = abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                                  start_monat="2026-01")
    abo_vertrag.beenden(db, vertrag_id=vertrag.id, end_monat="2026-08")

    assert _meiner(abo_abrechnung.offene_posten(db, "2026-08"), betrieb)
    assert _meiner(abo_abrechnung.offene_posten(db, "2026-09"), betrieb) == []


def test_ein_monat_vor_dem_beginn_wird_nicht_berechnet(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-09")

    assert _meiner(abo_abrechnung.offene_posten(db, "2026-08"), betrieb) == []


def test_nach_einem_wechsel_gilt_der_preis_des_damaligen_abos(db, betrieb):
    """Dieselbe Regel wie beim Kontingent: Der August rechnet mit dem Abo,
    das **im August** galt — sonst schriebe ein Wechsel die Rechnungen der
    Vergangenheit um."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-01")
    abo_vertrag.wechseln(db, lead_id=betrieb, produkt="ABO-PRO",
                         ab_monat="2026-09")

    august = _meiner(abo_abrechnung.offene_posten(db, "2026-08"), betrieb)[0]
    september = _meiner(abo_abrechnung.offene_posten(db, "2026-09"), betrieb)[0]

    assert august["netto_cent"] == 7900
    assert september["netto_cent"] == 14900


# ── Die Meldung ──────────────────────────────────────────────────────

def test_der_lauf_meldet_die_summe_und_den_vorbehalt(db, betrieb):
    from database import Benachrichtigung

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")

    ergebnis = abo_abrechnung.lauf(db, "2026-09")

    assert ergebnis["gemeldet"] is True
    meldung = db.query(Benachrichtigung).filter(
        Benachrichtigung.titel.like("Abrechnung 2026-09%")).first()
    assert meldung is not None
    assert "von Hand" in meldung.hinweis, "der Lauf stellt keine Rechnung aus"
    assert "Annahme" in meldung.hinweis, "der Preisvorbehalt gehoert dazu"


def test_eine_ueberschreitung_steht_vorn(db, betrieb):
    """Wer über sein Kontingent gearbeitet hat, ist das Gespräch **vor** der
    Rechnung — nicht die Reklamation danach."""
    from database import Benachrichtigung

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-08")
    abo_stunden.eintragen(db, lead_id=betrieb, stunden=3.0, wer="Test",
                          monat="2026-09")

    abo_abrechnung.lauf(db, "2026-09")

    meldung = db.query(Benachrichtigung).filter(
        Benachrichtigung.titel.like("Abrechnung 2026-09%")).first()
    assert meldung.hinweis.startswith("Über dem Kontingent")
    assert BETRIEB_NAME in meldung.hinweis


def test_ohne_posten_wird_nicht_gemeldet(db, betrieb):
    ergebnis = abo_abrechnung.lauf(db, "2019-05")
    assert ergebnis["posten"] == 0 and ergebnis["gemeldet"] is False


def test_zweimal_laufen_meldet_nur_einmal(db, betrieb):
    from database import Benachrichtigung

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")

    erst = abo_abrechnung.lauf(db, "2026-09")
    zweit = abo_abrechnung.lauf(db, "2026-09")

    assert erst["gemeldet"] is True and zweit["gemeldet"] is False
    assert db.query(Benachrichtigung).filter(
        Benachrichtigung.titel.like("Abrechnung 2026-09%")).count() == 1


# ── Anschluss ────────────────────────────────────────────────────────

def test_der_lauf_vergibt_keine_rechnungsnummer(db, betrieb):
    """**Die Zusicherung, auf die es ankommt.** Eine Rechnungsnummer ist
    fortlaufend; eine zweite für denselben Vorgang reisst eine Lücke in den
    Kreis. Der Lauf darf keine anlegen — das tut ein Mensch.
    """
    from sqlalchemy import text

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")
    vorher = db.execute(text("SELECT COUNT(*) FROM invoices")).scalar()

    abo_abrechnung.lauf(db, "2026-09")

    assert db.execute(text("SELECT COUNT(*) FROM invoices")).scalar() == vorher


def test_der_job_haengt_im_scheduler():
    """Ein Abrechnungslauf ohne Termin ist keiner."""
    import inspect

    from automations import scheduler as s

    quelle = inspect.getsource(s)
    assert '_run_abo_abrechnung' in quelle
    assert 'id="abo_abrechnung"' in quelle
    assert 'hour=5' in quelle, "vor den uebrigen Monatsjobs"
