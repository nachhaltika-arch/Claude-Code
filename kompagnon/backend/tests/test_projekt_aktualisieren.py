"""Was im Rumpf steht, wird zum Spaltennamen im SQL.

`PUT /api/projects/{id}` baut sein UPDATE aus den Schlüsseln des Rumpfes:

    sets = ", ".join(f"{k} = :{k}" for k in data)
    db.execute(text(f"UPDATE projects SET {sets} WHERE id = :pid"), data)

Die *Werte* sind gebunden, die *Namen* nicht. Ungeprüft bestimmt damit der
Aufrufer, was zwischen SET und WHERE landet — und schreibt nebenbei in jede
Spalte, die die Tabelle hat, auch in solche, die keine Oberfläche anbietet.

Deshalb: Jeder Schlüssel muss eine echte Spalte sein. Was das nicht ist, wird
abgewiesen — sichtbar, nicht still.
"""
import pytest


@pytest.fixture
def projekt_id(app, client, auth_headers):
    """Ein Projekt zum Ändern."""
    from database import SessionLocal, Lead, Project

    db = SessionLocal()
    try:
        betrieb = Lead(company_name="Pytest Änderungsbetrieb")
        db.add(betrieb)
        db.commit()
        db.refresh(betrieb)

        projekt = Project(lead_id=betrieb.id,
                          company_name="Pytest Änderungsbetrieb",
                          status="phase_1")
        db.add(projekt)
        db.commit()
        db.refresh(projekt)
        return projekt.id
    finally:
        db.close()


def test_eine_echte_spalte_wird_geschrieben(client, auth_headers, projekt_id):
    antwort = client.put(
        f"/api/projects/{projekt_id}",
        json={"company_name": "Neuer Name"},
        headers=auth_headers,
    )

    assert antwort.status_code == 200
    assert antwort.json()["company_name"] == "Neuer Name"


def test_ein_unbekanntes_feld_wird_abgewiesen(client, auth_headers, projekt_id):
    """Ein Tippfehler soll auffallen, nicht in einem SQL-Fehler enden."""
    antwort = client.put(
        f"/api/projects/{projekt_id}",
        json={"firmenname": "Neuer Name"},
        headers=auth_headers,
    )

    assert antwort.status_code == 400
    assert "firmenname" in antwort.json()["detail"]


def test_ein_schluessel_mit_sql_kommt_nicht_durch(client, auth_headers, projekt_id):
    """Der eigentliche Punkt: Der Schlüssel ist der Einlass, nicht der Wert."""
    antwort = client.put(
        f"/api/projects/{projekt_id}",
        json={"status = 'fertig', company_name": "egal"},
        headers=auth_headers,
    )

    assert antwort.status_code == 400


def test_gesperrte_schluessel_aendern_nichts(client, auth_headers, projekt_id):
    """`id` ist eine echte Spalte — die Sperre muss trotzdem greifen."""
    antwort = client.put(
        f"/api/projects/{projekt_id}",
        json={"id": 999999, "company_name": "Bleibt hier"},
        headers=auth_headers,
    )

    assert antwort.status_code == 200
    assert antwort.json()["id"] == projekt_id


def test_ein_leerer_rumpf_aendert_nichts(client, auth_headers, projekt_id):
    """Die Route wird auch nur lesend benutzt — das muss weiter gehen."""
    antwort = client.put(
        f"/api/projects/{projekt_id}", json={}, headers=auth_headers
    )

    assert antwort.status_code == 200
    assert antwort.json()["id"] == projekt_id
