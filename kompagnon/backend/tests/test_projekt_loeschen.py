"""Ein Projekt entfernen — mit allem, was daran hängt, und ohne das, was bleiben muss.

Bis heute gab es keinen einzigen Löschendpunkt für Projekte. Wer eines
loswerden wollte, musste SQL von Hand fahren — und genau das stand am
17.08.2026 an, weil ein Projekt 135 Tage lang jeden Morgen dieselbe Mail
ausgelöst hatte.

An `projects` hängen fünfzehn Tabellen, und sie zerfallen in zwei Gruppen:

  bleiben   Das Versandprotokoll (`email_logs`) ist der Nachweis, was wann an
            wen ging. Es überlebt das Projekt — nur der Verweis wird gelöst.
            Ebenso Kundenangaben (`briefings`) und Gespräche.

  gehen mit `customers` etwa hat einen NOT-NULL-Fremdschlüssel auf `projects`:
            Diese Zeilen KÖNNEN nicht bleiben. Darin stecken wiederkehrender
            Umsatz und CMS-Zugangsdaten — deshalb zählt der Endpunkt vorher
            und meldet hinterher, was er angefasst hat.

Die Reihenfolge ist keine Geschmacksfrage: Ein blankes `DELETE FROM projects`
scheitert an den Fremdschlüsseln.
"""
import pytest


@pytest.fixture
def betrieb_id(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Löschbetrieb")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


# `email_logs` steht nicht im Modell — die Tabelle entsteht erst beim Start in
# `main.py::_run_migrations`, und den lässt die Testeinrichtung bewusst aus.
# Für diesen Test wird sie deshalb angelegt: Genau an ihr hängt die Frage, ob
# das Versandprotokoll ein Löschen überlebt.
EMAIL_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS email_logs (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER,
  project_id INTEGER,
  recipient VARCHAR,
  subject VARCHAR,
  body TEXT,
  sent_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR DEFAULT 'sent'
)
"""


@pytest.fixture
def projekt_mit_anhang(app, betrieb_id):
    """Ein Projekt mit je einer Zeile aus beiden Gruppen."""
    from sqlalchemy import text
    from database import SessionLocal, Project, ProjectChecklist

    db = SessionLocal()
    try:
        projekt = Project(lead_id=betrieb_id, company_name="Pytest Löschprojekt",
                          status="phase_1")
        db.add(projekt)
        db.commit()
        db.refresh(projekt)

        db.add(ProjectChecklist(project_id=projekt.id, phase=1,
                                item_key="AKQ-01", item_label="Domain geprüft"))
        db.execute(text(EMAIL_LOGS_DDL))
        # `email_logs` steht nicht im Modell und überlebt deshalb das
        # Aufräumen nach dem Testlauf (`Base.metadata.drop_all`). Die
        # Projektnummern fangen danach wieder bei 1 an — ohne diese Zeile
        # zählt der Test Reste des vorigen Laufs mit.
        db.execute(text("DELETE FROM email_logs"))
        db.execute(
            text("INSERT INTO email_logs (lead_id, project_id, recipient, subject) "
                 "VALUES (:l, :p, :e, :s)"),
            {"l": betrieb_id, "p": projekt.id,
             "e": "kunde@example.com", "s": "Erinnerung"},
        )
        db.commit()
        return projekt.id
    finally:
        db.close()


def anzahl(tabelle: str, bedingung: str, wert) -> int:
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        return db.execute(
            text(f"SELECT count(*) FROM {tabelle} WHERE {bedingung} = :w"), {"w": wert}
        ).scalar()
    finally:
        db.close()


# ── Der Dienst ────────────────────────────────────────────────────────

def test_die_vorschau_zaehlt_ohne_zu_loeschen(app, projekt_mit_anhang):
    from database import SessionLocal
    from services.projekt_loeschen import zaehlen

    db = SessionLocal()
    try:
        bericht = zaehlen(db, [projekt_mit_anhang])
    finally:
        db.close()

    assert bericht["projekte"] == 1
    assert bericht["wird_geloescht"]["project_checklists"] == 1
    assert bericht["bleibt_erhalten"]["email_logs"] == 1
    assert anzahl("projects", "id", projekt_mit_anhang) == 1


def test_das_projekt_und_sein_anhang_verschwinden(app, projekt_mit_anhang):
    from database import SessionLocal
    from services.projekt_loeschen import entfernen

    db = SessionLocal()
    try:
        entfernen(db, [projekt_mit_anhang])
        db.commit()
    finally:
        db.close()

    assert anzahl("projects", "id", projekt_mit_anhang) == 0
    assert anzahl("project_checklists", "project_id", projekt_mit_anhang) == 0


def test_das_versandprotokoll_ueberlebt(app, projekt_mit_anhang, betrieb_id):
    """Der Nachweis, was wann an wen ging, darf nicht mit weggeräumt werden."""
    from database import SessionLocal
    from services.projekt_loeschen import entfernen

    db = SessionLocal()
    try:
        entfernen(db, [projekt_mit_anhang])
        db.commit()
    finally:
        db.close()

    assert anzahl("email_logs", "lead_id", betrieb_id) == 1
    assert anzahl("email_logs", "project_id", projekt_mit_anhang) == 0


def test_der_betrieb_bleibt_stehen(app, projekt_mit_anhang, betrieb_id):
    """Gelöscht wird das Projekt, nicht der Kunde."""
    from database import SessionLocal
    from services.projekt_loeschen import entfernen

    db = SessionLocal()
    try:
        entfernen(db, [projekt_mit_anhang])
        db.commit()
    finally:
        db.close()

    assert anzahl("leads", "id", betrieb_id) == 1


def test_eine_leere_liste_tut_nichts(app):
    from database import SessionLocal
    from services.projekt_loeschen import entfernen

    db = SessionLocal()
    try:
        bericht = entfernen(db, [])
    finally:
        db.close()

    assert bericht["projekte"] == 0


# ── Die Endpunkte ─────────────────────────────────────────────────────

def test_ein_projekt_loeschen(client, auth_headers, projekt_mit_anhang):
    antwort = client.delete(f"/api/projects/{projekt_mit_anhang}",
                            headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["projekte"] == 1
    assert anzahl("projects", "id", projekt_mit_anhang) == 0


def test_ein_projekt_das_es_nicht_gibt(client, auth_headers):
    antwort = client.delete("/api/projects/999999", headers=auth_headers)

    assert antwort.status_code == 404


def test_die_vorschau_als_endpunkt(client, auth_headers, projekt_mit_anhang):
    antwort = client.get(f"/api/projects/loeschvorschau?ids={projekt_mit_anhang}",
                         headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["projekte"] == 1
    assert anzahl("projects", "id", projekt_mit_anhang) == 1


def test_mehrere_auf_einmal(client, auth_headers, betrieb_id):
    from database import SessionLocal, Project

    db = SessionLocal()
    try:
        ids = []
        for i in range(3):
            p = Project(lead_id=betrieb_id, company_name=f"Massen {i}",
                        status="phase_1")
            db.add(p)
            db.commit()
            db.refresh(p)
            ids.append(p.id)
    finally:
        db.close()

    antwort = client.post("/api/projects/loeschen", json={"ids": ids},
                          headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["projekte"] == 3
    assert all(anzahl("projects", "id", i) == 0 for i in ids)


def test_massenloeschen_ohne_ids_wird_abgewiesen(client, auth_headers):
    """Ein leerer Rumpf darf nicht versehentlich alles bedeuten."""
    antwort = client.post("/api/projects/loeschen", json={"ids": []},
                          headers=auth_headers)

    assert antwort.status_code == 400


def test_loeschen_verlangt_adminrechte(client, kunde_headers, projekt_mit_anhang):
    antwort = client.delete(f"/api/projects/{projekt_mit_anhang}",
                            headers=kunde_headers)

    assert antwort.status_code == 403
    assert anzahl("projects", "id", projekt_mit_anhang) == 1


# ── Der Weg über den Betrieb ──────────────────────────────────────────

def test_einen_betrieb_mit_kundenzeile_loeschen(client, auth_headers,
                                                betrieb_id, projekt_mit_anhang):
    """Vorher scheiterte das am NOT-NULL-Fremdschlüssel von `customers`.

    `DELETE /api/leads/{id}` räumte vier Tabellen ab und löschte dann die
    Projekte. Sobald ein Projekt eine Kundenzeile hatte, brach das mit einem
    Fremdschlüsselfehler ab — und mit ihm die ganze Löschung.
    """
    from database import SessionLocal, Customer

    db = SessionLocal()
    try:
        db.add(Customer(project_id=projekt_mit_anhang, recurring_revenue=99.0))
        db.commit()
    finally:
        db.close()

    antwort = client.delete(f"/api/leads/{betrieb_id}", headers=auth_headers)

    assert antwort.status_code == 200
    assert anzahl("leads", "id", betrieb_id) == 0
    assert anzahl("projects", "id", projekt_mit_anhang) == 0
    assert anzahl("customers", "project_id", projekt_mit_anhang) == 0


def test_loeschen_ohne_anmeldung_geht_nicht(client, projekt_mit_anhang):
    antwort = client.delete(f"/api/projects/{projekt_mit_anhang}")

    assert antwort.status_code in (401, 403)
    assert anzahl("projects", "id", projekt_mit_anhang) == 1
