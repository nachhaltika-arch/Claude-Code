"""Was der Code einem Datensatz zuweist, muss auch in der Datenbank landen.

Befund vom 18.08.2026. Der Start zieht 370 Spalten per `ALTER TABLE … ADD
COLUMN IF NOT EXISTS` nach; **92 davon stehen in keinem Modell**. Solange
niemand sie anfasst, ist das folgenlos. Zwoelf werden aber zugewiesen:

    lead.onboarding_completed = True      # leads.py:887
    customer.pagespeed_mobile_score = …   # customers.py:255
    lead.unread_messages = 0              # messages.py:135
    proj.current_phase = …                # briefings.py:77

SQLAlchemy wirft dabei **nichts**. Der Wert landet auf dem Python-Objekt und
verschwindet beim naechsten Laden. Am Objekt geprueft: gesetzt, committet,
neu geladen → `True`; in der Datenbank steht `False`.

Praktisch heisst das: Ein Kunde, der sein Onboarding abgeschlossen hat, wird
beim naechsten Anmelden wieder danach gefragt. Jede PageSpeed-Messung wird
weggeworfen. Der Zaehler ungelesener Nachrichten geht nie auf null.

Verwandt mit [[migration-trap-main-py]]: Dort fehlte die Spalte in der
Datenbank, hier im Modell. Beides faellt nicht auf, weil beides nicht knallt.
"""
from datetime import datetime

import pytest
from sqlalchemy import text


def _neu_laden(db, modell, objekt_id):
    db.expire_all()
    return db.query(modell).filter(modell.id == objekt_id).first()


def test_abgeschlossenes_onboarding_bleibt_abgeschlossen(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        betrieb = Lead(company_name="Spaltenprobe Betrieb")
        db.add(betrieb)
        db.commit()

        betrieb.onboarding_completed = True
        betrieb.onboarding_completed_at = datetime.utcnow()
        db.commit()

        in_der_datenbank = db.execute(
            text("SELECT onboarding_completed FROM leads WHERE id = :i"),
            {"i": betrieb.id},
        ).scalar()

        assert in_der_datenbank is True, (
            "Das Kennzeichen steht nur im Arbeitsspeicher — der Kunde wird "
            "beim naechsten Anmelden wieder nach seinem Onboarding gefragt."
        )
    finally:
        db.close()


def test_der_zaehler_ungelesener_nachrichten_bleibt_stehen(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        betrieb = Lead(company_name="Spaltenprobe Nachrichten")
        db.add(betrieb)
        db.commit()

        betrieb.unread_messages = 7
        db.commit()

        assert db.execute(
            text("SELECT unread_messages FROM leads WHERE id = :i"), {"i": betrieb.id},
        ).scalar() == 7
    finally:
        db.close()


@pytest.mark.parametrize("spalte,wert", [
    ("pagespeed_mobile_score", 84),
    ("pagespeed_desktop_score", 91),
    ("pagespeed_lcp_mobile", 2.4),
])
def test_pagespeed_werte_werden_gespeichert(app, spalte, wert):
    from database import SessionLocal, Customer, Lead, Project

    db = SessionLocal()
    try:
        betrieb = Lead(company_name="Spaltenprobe PageSpeed")
        db.add(betrieb)
        db.commit()
        projekt = Project(lead_id=betrieb.id, status="briefing")
        db.add(projekt)
        db.commit()
        kunde = Customer(project_id=projekt.id)
        db.add(kunde)
        db.commit()

        setattr(kunde, spalte, wert)
        db.commit()

        gespeichert = db.execute(
            text(f"SELECT {spalte} FROM customers WHERE id = :i"), {"i": kunde.id},
        ).scalar()
        assert gespeichert == pytest.approx(wert), (
            f"{spalte} wurde gemessen und nicht gespeichert"
        )
    finally:
        db.close()


def test_die_projektphase_bleibt_erhalten(app):
    from database import SessionLocal, Lead, Project

    db = SessionLocal()
    try:
        betrieb = Lead(company_name="Spaltenprobe Phase")
        db.add(betrieb)
        db.commit()
        projekt = Project(lead_id=betrieb.id, status="briefing")
        db.add(projekt)
        db.commit()

        projekt.current_phase = 4
        db.commit()

        assert db.execute(
            text("SELECT current_phase FROM projects WHERE id = :i"), {"i": projekt.id},
        ).scalar() == 4
    finally:
        db.close()
