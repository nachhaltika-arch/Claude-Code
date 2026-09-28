# -*- coding: utf-8 -*-
"""Die Umbenennung „Homepage Standard" → „Website Standard" erreicht die Audits.

**Der Anlass (L-212, 28.09.2026).** Seit dem 18.09. stand in
`migrations_runtime.py` ein `UPDATE audits SET level = …` — die Tabelle heißt
aber `audit_results`. Der Startlauf verbuchte das als „übersprungen" auf
INFO-Ebene, zehn Tage lang ohne Folgen im Protokoll. Altzeilen mit
„Homepage Standard Gold" blieben stehen, und das Frontend findet sie in
`STUFEN` nicht mehr: Stufe ohne Zeichen, Filter greifen daneben.

**Am Gegenstand geprüft, nicht am Quelltext.** Ein Test, der nur nach dem
richtigen Tabellennamen im SQL sucht, wäre auch grün, wenn die Anweisung an
anderer Stelle scheitert. Hier wird eine echte Altzeile angelegt, die
Migration gefahren und die Zeile danach gelesen.
"""
import pytest

ALTE_STUFE = "Homepage Standard Gold"
NEUE_STUFE = "Website Standard Gold"
MARKE = "stufenname-migration.test"


@pytest.fixture
def altzeilen(app):
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        audit_id = db.execute(text(
            "INSERT INTO audit_results (website_url, company_name, level) "
            "VALUES (:url, 'Stufenname Testbetrieb', :stufe) RETURNING id"
        ), {"url": f"https://{MARKE}", "stufe": ALTE_STUFE}).scalar_one()
        db.commit()
        yield audit_id
    finally:
        db.rollback()
        db.execute(text("DELETE FROM audit_results WHERE website_url = :url"),
                   {"url": f"https://{MARKE}"})
        db.commit()
        db.close()


def _stufe(audit_id):
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        return db.execute(text("SELECT level FROM audit_results WHERE id = :id"),
                          {"id": audit_id}).scalar_one()
    finally:
        db.close()


def test_die_migration_benennt_die_audit_stufe_um(altzeilen):
    from migrations_runtime import run_migrations

    # Gegenprobe: Die Altzeile steht wirklich da, bevor migriert wird.
    assert _stufe(altzeilen) == ALTE_STUFE

    run_migrations()

    assert _stufe(altzeilen) == NEUE_STUFE


def test_ein_zweiter_lauf_aendert_nichts_mehr(altzeilen):
    from migrations_runtime import run_migrations

    run_migrations()
    run_migrations()

    assert _stufe(altzeilen) == NEUE_STUFE
