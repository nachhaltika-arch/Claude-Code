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


# ── Wer die Anfrage stellen darf ─────────────────────────────────────
#
# `POST /api/projects/{id}/request-approval` gibt in seiner Antwort den
# Freigabe-Token zurueck, und mit dem laesst sich ueber
# `POST /api/projects/approve-content/{token}` **ohne Anmeldung** freigeben.
# Wer die Anfrage stellen darf, kann sich die Freigabe also selbst erteilen.
#
# Deshalb bleibt die Route bei `require_admin` — zusaetzlich zu der Sperre,
# die der Router ohnehin traegt (`dependencies=[Depends(require_innendienst)]`,
# projects.py Zeile 121). Am 22.08.2026 gemessen, wen die beiden Sperren
# zusammen ausschliessen:
#
#   superadmin, admin   view_leads=True    kommen durch
#   auditor             view_leads=True    kommt durch den Router, scheitert
#                                          an `require_admin` — 403
#   nutzer, kunde       view_leads=False   scheitern schon am Router
#
# Der Auditor ist der einzige, den die Verschaerfung wirklich kostet. Das ist
# eine bewusste Abwaegung und keine Nachlaessigkeit: Ein Token, der ohne
# Anmeldung gilt, wiegt schwerer als ein Knopf, den eine Rolle nicht erreicht.


def test_der_kunde_kommt_an_die_anfrage_nicht_heran(client, kunde_headers, eigenes_projekt):
    """Auch am eigenen Projekt nicht — der Token waere der eigene Freibrief."""
    antwort = client.post(
        f"/api/projects/{eigenes_projekt}/request-approval",
        json={"topic": "DNS-Einrichtung", "notes": ""},
        headers=kunde_headers,
    )

    assert antwort.status_code == 403


# ── Die zweite Haelfte des Kundenportal-Ablaufs ──────────────────────
#
# Bis zum 22.08.2026 lagen zwei verschiedene Freigabe-Verfahren auf
# `POST /{project_id}/request-approval`:
#
#   Zeile 1041   Token-Link ohne Anmeldung, schreibt `content_approval_token`
#   Zeile 3252   seitenweise Freigabe im Kundenportal, schreibt
#                `content_freigaben`
#
# FastAPI nimmt bei gleichem Pfad die zuerst registrierte Funktion. Die zweite
# war damit unerreichbar — und mit ihr die **Schreib**-Haelfte des
# Kundenportal-Ablaufs. `confirm_approval` weiter unten ist erreichbar und
# wird von `customer/Freigaben.jsx` aufgerufen, aber es entstand nie ein
# Eintrag mit `status: "angefragt"`, den der Kunde haette entscheiden koennen.
#
# Die seitenweise Freigabe hat jetzt `POST /{project_id}/request-page-approval`.


def test_beide_freigabe_verfahren_haben_eine_eigene_adresse(app):
    """Gezaehlt wird ueber `openapi()`, nicht ueber `app.routes`.

    `app.routes` liefert unter Starlette 1.4 nur rund 70 Eintraege — die
    eingebundenen Unter-Router fehlen darin. Wer damit zaehlt, misst das
    Werkzeug statt den Gegenstand und haelt eine vorhandene Route fuer
    verschwunden. `app.openapi()["paths"]` kennt alle rund 380.
    """
    pfade = app.openapi()["paths"]

    assert "/api/projects/{project_id}/request-approval" in pfade
    assert "/api/projects/{project_id}/request-page-approval" in pfade


def test_die_seitenweise_anfrage_traegt_sich_wirklich_ein(client, auth_headers, fremdes_projekt):
    """Eine tote Route ist eine ungepruefte Route (L-68).

    Deshalb wird hier nicht die Registrierung geprueft, sondern die Wirkung:
    Nach der Anfrage steht der Eintrag in `content_freigaben` und traegt den
    Zustand, den `confirm_approval` spaeter entscheidet.
    """
    antwort = client.post(
        f"/api/projects/{fremdes_projekt}/request-page-approval",
        json={"seite_id": "startseite", "topic": "Startseite", "notes": ""},
        headers=auth_headers,
    )

    assert antwort.status_code == 200, antwort.text[:200]
    assert antwort.json()["freigaben"]["startseite"]["status"] == "angefragt"


def test_und_der_kunde_kann_sie_danach_entscheiden(client, auth_headers, kunde_headers, eigenes_projekt):
    """Die Kette, an der es lag: anfragen → im Portal entscheiden."""
    client.post(
        f"/api/projects/{eigenes_projekt}/request-page-approval",
        json={"seite_id": "kontakt", "topic": "Kontaktseite"},
        headers=auth_headers,
    )

    antwort = client.post(
        f"/api/projects/{eigenes_projekt}/confirm-approval",
        json={"seite_id": "kontakt", "bestaetigt": True},
        headers=kunde_headers,
    )

    assert antwort.status_code == 200
    assert antwort.json()["freigaben"]["kontakt"]["status"] == "freigegeben"
