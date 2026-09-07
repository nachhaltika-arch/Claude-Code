# -*- coding: utf-8 -*-
"""Die Ground Page wird abgelegt, nicht nur erzeugt (L-179).

**Der Befund vom 07.09.2026.** `routers/projects_sichtbarkeit.py` schreibt das
Ergebnis der Ground-Page-Erzeugung mit
`INSERT INTO website_content (sitemap_page_id, ki_content, …)`. Diese Tabelle
gibt es nicht: kein Modell fuehrt sie, keine Migration legt sie an, und lokal
steht in `pg_tables` nur `website_content_cache` — eine voellig andere Tabelle
mit anderen Spalten, also kein Tippfehler.

**Warum das teurer ist als ein fehlgeschlagener Aufruf.** Die Reihenfolge im
Code ist: Claude fragen, Antwort zerlegen, JSON-LD bauen — **dann** ablegen.
Die Ablage ist der letzte Schritt. Faellt sie aus, ist der KI-Aufruf bereits
bezahlt und das Ergebnis fertig; es geht nur verloren. Der Anrufer bekommt
`500 Ground Page Generierung fehlgeschlagen` — eine falsche Diagnose, denn die
Generierung hat funktioniert.

**Warum nicht in `sitemap_pages` umgebogen wird.** Die Nachbarspalten dort
(`ki_h1`, `ki_hero_text`, `ki_abschnitt_text`, `ki_cta`) tragen die Texte
einer gewoehnlichen Seite. Die Ground Page ist etwas anderes: ein
strukturiertes Dokument fuer KI-Systeme mit Fakten, fuenf Fragen und
Antworten, Vertrauensangaben und JSON-LD. Eine eigene Zeile je Seite mit
einem JSON-Feld ist dafuer der richtige Entwurf — er war nur nie angelegt.
"""
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))

import pytest
from sqlalchemy import text

SPALTEN = {"sitemap_page_id", "ki_content", "content_generated", "updated_at"}


@pytest.fixture
def db_session(app):
    """Eine Sitzung auf der Testdatenbank — `app` sorgt dafuer, dass die
    Migrationen vorher gelaufen sind."""
    from database import SessionLocal

    sitzung = SessionLocal()
    try:
        yield sitzung
        sitzung.commit()
    finally:
        sitzung.close()


def test_die_tabelle_existiert(db_session):
    vorhanden = db_session.execute(text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name = 'website_content'")).fetchone()
    assert vorhanden, (
        "Tabelle `website_content` fehlt — `projects_sichtbarkeit.py` schreibt "
        "darauf, und der Schreibversuch ist der letzte Schritt nach einem "
        "bezahlten KI-Aufruf.")


def test_sie_traegt_die_spalten_die_der_code_schreibt(db_session):
    spalten = {r[0] for r in db_session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'website_content'")).fetchall()}
    assert SPALTEN <= spalten, f"fehlende Spalten: {sorted(SPALTEN - spalten)}"


def test_der_konflikt_hat_seinen_eindeutigen_schluessel(db_session):
    """`ON CONFLICT (sitemap_page_id)` braucht eine eindeutige Zusicherung.

    Ohne sie scheitert die Anweisung mit „there is no unique or exclusion
    constraint matching the ON CONFLICT specification" — und zwar erst zur
    Laufzeit, nach dem KI-Aufruf. Eine Tabelle anzulegen und diesen Teil zu
    vergessen waere derselbe Fehler eine Ebene tiefer.
    """
    eindeutig = db_session.execute(text("""
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'website_content'
          AND indexdef ILIKE '%UNIQUE%'
          AND indexdef ILIKE '%sitemap_page_id%'""")).fetchone()
    assert eindeutig, "keine eindeutige Zusicherung auf sitemap_page_id"


def test_die_anweisung_laeuft_wirklich_durch(db_session):
    """Am Gegenstand geprueft, nicht am Schema.

    Drei gruene Schemapruefungen sagen noch nicht, dass die Anweisung des
    Routers laeuft. Hier laeuft sie — woertlich dieselbe, mit demselben
    `ON CONFLICT`, zweimal hintereinander.
    """
    seite = db_session.execute(text(
        "SELECT id FROM sitemap_pages LIMIT 1")).fetchone()
    if not seite:
        db_session.execute(text(
            "INSERT INTO sitemap_pages (lead_id, page_name, page_type) "
            "VALUES (NULL, 'Pruefseite', 'ground')"))
        seite = db_session.execute(text(
            "SELECT id FROM sitemap_pages ORDER BY id DESC LIMIT 1")).fetchone()

    anweisung = text("""
        INSERT INTO website_content (sitemap_page_id, ki_content, content_generated, updated_at)
        VALUES (:pid, :content, TRUE, NOW())
        ON CONFLICT (sitemap_page_id)
        DO UPDATE SET ki_content = EXCLUDED.ki_content,
                      content_generated = TRUE,
                      updated_at = NOW()
    """)
    db_session.execute(anweisung, {"pid": seite[0], "content": '{"a": 1}'})
    db_session.execute(anweisung, {"pid": seite[0], "content": '{"a": 2}'})
    inhalt = db_session.execute(text(
        "SELECT ki_content FROM website_content WHERE sitemap_page_id = :pid"),
        {"pid": seite[0]}).scalar()
    assert '"a": 2' in inhalt, "der zweite Lauf hat nicht ueberschrieben"
    db_session.execute(text(
        "DELETE FROM website_content WHERE sitemap_page_id = :pid"), {"pid": seite[0]})
