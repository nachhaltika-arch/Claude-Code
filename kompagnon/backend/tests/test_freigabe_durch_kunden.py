"""Der Kunde muss seine Freigabe auch erteilen können.

Befund vom 17.08.2026: `POST /api/projects/{id}/confirm-approval` verlangte
`require_admin` — und genau diesen Endpunkt ruft die Kundenseite
`customer/Freigaben.jsx` auf. Der Eintrag „Freigaben" steht im Kundenmenü,
die Anfrage-Mail schreibt „melden Sie sich in Ihrem Kundenportal an, um die
Freigabe zu erteilen", und dort war der Knopf wirkungslos.

Unsichtbar war es, weil die Seite `res.ok` nicht prüfte: Der 403 landete in
einem `console.error`, danach lud die Seite neu und zeigte weiter
„ausstehend". Dieselbe Bauart wie Lücke L-36 — ein Fehler, den niemand sieht,
ist ein Fehler, der bleibt.

Die Grenze ist nicht „Kunde nein", sondern „nur das eigene Projekt".
"""
import pytest


# `content_freigaben` steht nicht im Modell — die Spalte kommt erst beim Start
# aus `main.py::_run_migrations`, und den lässt die Testeinrichtung aus.
SPALTE_NACHZIEHEN = (
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_freigaben TEXT"
)


def _projekt_anlegen(lead_id: int, name: str, freigaben: str = None) -> int:
    import json
    from sqlalchemy import text
    from database import SessionLocal, Project

    db = SessionLocal()
    try:
        db.execute(text(SPALTE_NACHZIEHEN))
        db.commit()

        projekt = Project(lead_id=lead_id, company_name=name, status="phase_3")
        db.add(projekt)
        db.commit()
        db.refresh(projekt)

        if freigaben:
            db.execute(
                text("UPDATE projects SET content_freigaben = :cf WHERE id = :id"),
                {"cf": freigaben, "id": projekt.id},
            )
            db.commit()
        return projekt.id
    finally:
        db.close()


@pytest.fixture
def eigenes_projekt(app, kunde_user):
    """Ein Projekt am Betrieb des Kunden, mit einer offenen Freigabe."""
    import json

    return _projekt_anlegen(
        kunde_user.lead_id, "Pytest Kundenbetrieb",
        json.dumps({"startseite": {"status": "angefragt"}}),
    )


@pytest.fixture
def fremdes_projekt(app, fremder_betrieb):
    return _projekt_anlegen(fremder_betrieb, "Pytest Fremdprojekt")


def test_der_kunde_gibt_die_eigene_seite_frei(client, kunde_headers, eigenes_projekt):
    antwort = client.post(
        f"/api/projects/{eigenes_projekt}/confirm-approval",
        json={"seite_id": "startseite", "bestaetigt": True},
        headers=kunde_headers,
    )

    assert antwort.status_code == 200
    assert antwort.json()["freigaben"]["startseite"]["status"] == "freigegeben"


def test_der_kunde_kann_auch_ablehnen(client, kunde_headers, eigenes_projekt):
    antwort = client.post(
        f"/api/projects/{eigenes_projekt}/confirm-approval",
        json={"seite_id": "startseite", "bestaetigt": False},
        headers=kunde_headers,
    )

    assert antwort.status_code == 200
    assert antwort.json()["freigaben"]["startseite"]["status"] == "abgelehnt"


def test_der_kunde_kommt_nicht_an_fremde_projekte(client, kunde_headers, fremdes_projekt):
    antwort = client.post(
        f"/api/projects/{fremdes_projekt}/confirm-approval",
        json={"seite_id": "startseite", "bestaetigt": True},
        headers=kunde_headers,
    )

    assert antwort.status_code == 403


def test_der_innendienst_darf_weiterhin(client, auth_headers, fremdes_projekt):
    """Freigaben werden auch im Gespräch aufgenommen und nachgetragen."""
    antwort = client.post(
        f"/api/projects/{fremdes_projekt}/confirm-approval",
        json={"seite_id": "startseite", "bestaetigt": True},
        headers=auth_headers,
    )

    assert antwort.status_code == 200


def test_ohne_anmeldung_gar_nicht(client, eigenes_projekt):
    antwort = client.post(
        f"/api/projects/{eigenes_projekt}/confirm-approval",
        json={"seite_id": "startseite", "bestaetigt": True},
    )

    assert antwort.status_code in (401, 403)
