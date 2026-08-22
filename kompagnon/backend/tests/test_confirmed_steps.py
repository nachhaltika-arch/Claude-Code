"""Ein bestätigter Schritt muss den Reload überleben.

Gefunden am 2026-08-13 beim Versuch, die Design-Ansicht im Browser-Test zu
erreichen: `POST /confirm-step` antwortet mit `{"saved": true}` und den
bestätigten Schritten — in der Datenbank steht danach weiter `{}`. Der Grund
ist die Falle, die dieses Projekt schon einmal getroffen hat: Die Spalte
`steps_confirmed` legt `migrations_runtime.py::run_migrations` per rohem SQL an, das
ORM-Modell kennt sie nicht. `project.steps_confirmed = …` setzt dann nur ein
Attribut am Python-Objekt, `db.commit()` schreibt nichts, und die Antwort
liest denselben Speicher zurück.

Die Folge im Alltag: Der Editor gibt nur den nächsten Schritt nach der letzten
lückenlosen Kette frei. Bestätigungen gehen verloren, also bleiben Wireframe,
Style-Guide und Design gesperrt — und niemand sieht einen Fehler.
"""
import pytest


@pytest.fixture
def projekt(client, auth_headers):
    from database import Lead, Project, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Schritte GmbH", email="schritte@pytest.local")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        p = Project(lead_id=lead.id)
        db.add(p)
        db.commit()
        db.refresh(p)
        ids = (lead.id, p.id)
    finally:
        db.close()

    yield ids[1]

    db = SessionLocal()
    try:
        db.query(Project).filter(Project.id == ids[1]).delete()
        db.query(Lead).filter(Lead.id == ids[0]).delete()
        db.commit()
    finally:
        db.close()


def test_bestaetigter_schritt_steht_beim_naechsten_laden_noch_da(client, auth_headers,
                                                                 projekt):
    speichern = client.post(f"/api/projects/{projekt}/confirm-step",
                            headers=auth_headers, json={"step_id": "audit"})
    assert speichern.status_code == 200, speichern.text
    assert speichern.json()["saved"] is True

    gelesen = client.get(f"/api/projects/{projekt}/confirmed-steps", headers=auth_headers)

    assert gelesen.status_code == 200
    assert gelesen.json().get("audit", {}).get("confirmed") is True, (
        "Die Bestätigung ist zwischen Antwort und Datenbank verschwunden — "
        "kennt das ORM-Modell die Spalte `steps_confirmed`?")


def test_mehrere_schritte_sammeln_sich(client, auth_headers, projekt):
    for schritt in ("briefing-unternehmen", "audit", "sitemap-ki"):
        client.post(f"/api/projects/{projekt}/confirm-step", headers=auth_headers,
                    json={"step_id": schritt})

    bestaetigt = client.get(f"/api/projects/{projekt}/confirmed-steps",
                            headers=auth_headers).json()

    assert set(bestaetigt) == {"briefing-unternehmen", "audit", "sitemap-ki"}


def test_ohne_schritt_kein_eintrag(client, auth_headers, projekt):
    antwort = client.post(f"/api/projects/{projekt}/confirm-step",
                          headers=auth_headers, json={"step_id": "  "})

    assert antwort.status_code == 400
