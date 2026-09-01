# -*- coding: utf-8 -*-
"""Der Termingeber fuer das Quartals-Re-Audit (L-101, letzter Teil).

**Was auf dem Spiel steht.** ABO-BAS und ABO-PRO sagen ein Quartals-Re-Audit
zu, und G4 verspricht Nachbesserung **ohne Berechnung**, wenn der Wert faellt.
Ein Termin, an den niemand erinnert, ist eine Zusage, die man bricht, ohne es
zu merken — und zwar genau bei dem Kunden, der schon unzufrieden ist.

**Der Job gibt kein Geld aus.** Er stellt fest, wer dran ist, und meldet es;
die Pruefung selbst loest ein Mensch aus. Die Tests halten beide Haelften
fest: dass gemeldet wird, wo etwas ansteht, und dass **nicht** gemeldet wird,
wo nichts ansteht — „nichts zu tun" als Benachrichtigung ist der schnellste
Weg, dass die naechste echte ueberlesen wird.
"""
from datetime import datetime

import pytest

from services import abo_vertrag, quartals_reaudit

BETRIEB_NAME = "Elektro Quartal-Nur-Im-Test"

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
    from database import AuditResult, Benachrichtigung, Lead
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
        db.query(AuditResult).filter(AuditResult.lead_id == kennung).delete()
        db.query(AboVertrag).filter(AboVertrag.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()


@pytest.fixture(autouse=True)
def _meldungen_aufraeumen(db):
    """Die Meldung haengt an keinem Betrieb — sie muss eigens weg."""
    from database import Benachrichtigung
    yield
    db.query(Benachrichtigung).filter(
        Benachrichtigung.art == quartals_reaudit.ART).delete()
    db.commit()


def _namen(faellig):
    return [f["betrieb"] for f in faellig]


# ── Die Quartalsrechnung ─────────────────────────────────────────────

@pytest.mark.parametrize("monat,erwartet", [
    (1, "Q1"), (3, "Q1"), (4, "Q2"), (6, "Q2"),
    (7, "Q3"), (9, "Q3"), (10, "Q4"), (12, "Q4"),
])
def test_jeder_monat_faellt_in_sein_quartal(monat, erwartet):
    """Die Grenzen sind der Ort, an dem eine Handrechnung danebenliegt."""
    assert quartals_reaudit.quartal_von(
        datetime(2026, monat, 15)) == f"2026-{erwartet}"


def test_der_quartalsbeginn_ist_der_erste_seines_monats():
    assert quartals_reaudit.quartalsbeginn(
        datetime(2026, 8, 31)) == datetime(2026, 7, 1)
    assert quartals_reaudit.quartalsbeginn(
        datetime(2026, 1, 1)) == datetime(2026, 1, 1)


# ── Wer ist faellig ──────────────────────────────────────────────────

def test_ohne_vertrag_ist_niemand_faellig(db, betrieb):
    """Ein Re-Audit ist zugesagt, wo ein Abo gilt. Sonst waere es eine
    Leistung, fuer die niemand zahlt — und die Meldung nennte Betriebe, die
    nichts erwarten."""
    faellig = quartals_reaudit.faellige_betriebe(db, datetime(2026, 7, 1))
    assert BETRIEB_NAME not in _namen(faellig)


def test_mit_laufendem_vertrag_und_ohne_pruefung_ist_er_faellig(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-01")

    faellig = quartals_reaudit.faellige_betriebe(db, datetime(2026, 7, 1))

    treffer = [f for f in faellig if f["lead_id"] == betrieb]
    assert treffer and treffer[0]["produkt"] == "ABO-PRO"


def test_eine_pruefung_im_quartal_nimmt_die_faelligkeit(db, betrieb):
    from database import AuditResult

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-01")
    db.add(AuditResult(lead_id=betrieb, status="completed",
                       website_url="https://quartal.example",
                       company_name=BETRIEB_NAME,
                       created_at=datetime(2026, 8, 3)))
    db.commit()

    faellig = quartals_reaudit.faellige_betriebe(db, datetime(2026, 9, 1))

    assert betrieb not in [f["lead_id"] for f in faellig]


def test_eine_pruefung_aus_dem_vorquartal_zaehlt_nicht(db, betrieb):
    """**Der Kern des Termins.** Eine Pruefung vom Juni loest das Re-Audit
    fuer das dritte Quartal nicht ein — sonst waere die Zusage „einmal" statt
    „vierteljaehrlich"."""
    from database import AuditResult

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-01")
    db.add(AuditResult(lead_id=betrieb, status="completed",
                       website_url="https://quartal.example",
                       company_name=BETRIEB_NAME,
                       created_at=datetime(2026, 6, 30)))
    db.commit()

    faellig = quartals_reaudit.faellige_betriebe(db, datetime(2026, 7, 1))

    assert betrieb in [f["lead_id"] for f in faellig]


def test_ein_beendeter_vertrag_macht_nicht_mehr_faellig(db, betrieb):
    vertrag = abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                                  start_monat="2026-01")
    abo_vertrag.beenden(db, vertrag_id=vertrag.id, end_monat="2026-05")

    faellig = quartals_reaudit.faellige_betriebe(db, datetime(2026, 7, 1))

    assert betrieb not in [f["lead_id"] for f in faellig]


# ── Die Meldung ──────────────────────────────────────────────────────

def test_der_lauf_meldet_was_ansteht(db, betrieb):
    from database import Benachrichtigung

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-01")

    ergebnis = quartals_reaudit.lauf(db, datetime(2026, 7, 1))

    assert ergebnis["gemeldet"] is True
    assert ergebnis["quartal"] == "2026-Q3"
    meldung = db.query(Benachrichtigung).filter(
        Benachrichtigung.art == quartals_reaudit.ART).first()
    assert meldung is not None
    assert "2026-Q3" in meldung.titel
    assert BETRIEB_NAME in meldung.hinweis
    assert meldung.ziel == quartals_reaudit.ZIEL
    assert "G4" in meldung.hinweis, "der Grund, warum es eilt, gehoert dazu"


def test_ohne_faelligkeit_wird_nicht_gemeldet(db, betrieb):
    """**Die wichtigere Haelfte.** „Nichts zu tun" als Benachrichtigung ist
    der schnellste Weg, dass die naechste echte ueberlesen wird.

    **Gemessen in einem Quartal, in dem es keine Vertraege geben kann.** Der
    erste Entwurf nahm 2026-Q3 und war rot — nicht wegen eines Fehlers,
    sondern weil ein Vertrag aus einem Nachbartest noch stand. Ein Test, der
    ueber den ganzen Bestand urteilt, misst die anderen mit.
    """
    from database import Benachrichtigung

    ergebnis = quartals_reaudit.lauf(db, datetime(2020, 7, 1))

    assert ergebnis["faellig"] == 0
    assert ergebnis["gemeldet"] is False
    assert db.query(Benachrichtigung).filter(
        Benachrichtigung.art == quartals_reaudit.ART,
        Benachrichtigung.titel.like("%2020-Q3%")).count() == 0


def test_zweimal_laufen_meldet_nur_einmal(db, betrieb):
    """Ein Neustart am Ersten, ein Aufruf von Hand — eine Glocke, der man
    nicht glaubt, schaltet man ab."""
    from database import Benachrichtigung

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-01")

    erst = quartals_reaudit.lauf(db, datetime(2026, 7, 1))
    zweit = quartals_reaudit.lauf(db, datetime(2026, 7, 1))

    assert erst["gemeldet"] is True and zweit["gemeldet"] is False
    assert db.query(Benachrichtigung).filter(
        Benachrichtigung.art == quartals_reaudit.ART).count() == 1


def test_ein_neues_quartal_meldet_wieder(db, betrieb):
    from database import Benachrichtigung

    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-01")

    quartals_reaudit.lauf(db, datetime(2026, 7, 1))
    zweites = quartals_reaudit.lauf(db, datetime(2026, 10, 1))

    assert zweites["gemeldet"] is True
    assert db.query(Benachrichtigung).filter(
        Benachrichtigung.art == quartals_reaudit.ART).count() == 2


# ── Anschluss ────────────────────────────────────────────────────────

def test_die_art_ist_bekannt():
    """Sonst legt `melden` sie zwar ab, schreibt aber eine Warnung ins
    Protokoll — und ein Protokoll voller Fehlalarme ist eines, in dem der
    echte Fehler untergeht."""
    from services.benachrichtigungen import ARTEN

    assert quartals_reaudit.ART in ARTEN


def test_der_job_haengt_im_scheduler():
    """**Ein Termingeber ohne Termin ist keiner.** Genau diese Klasse hat den
    Bestand fuenfmal getroffen: gebaut, nicht angeschlossen."""
    import inspect

    from automations import scheduler as s

    quelle = inspect.getsource(s)
    assert '_run_quartals_reaudit' in quelle
    assert 'id="quartals_reaudit"' in quelle
    assert 'month="1,4,7,10"' in quelle, "vierteljaehrlich, nicht monatlich"
