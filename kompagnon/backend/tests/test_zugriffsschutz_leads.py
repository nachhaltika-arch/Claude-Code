"""Kundendaten sind nicht ohne Anmeldung zu haben.

Befund vom 14.08.2026: `GET /api/leads/` lieferte produktiv den vollständigen
Leadbestand — Firmen, Namen, Telefonnummern, E-Mail-Adressen, Notizen — an
jeden, der die Adresse kannte. Offen waren 31 der 42 Routen des Lead-Routers
und alle sieben des Kunden-Routers, darunter Löschen, Ändern, der CSV-Export
und Läufe, die Geld kosten.

Die Ursache war die Richtung: Die Anmeldung hing an der einzelnen Route, und
wer eine hinzufügte und sie vergaß, öffnete sie. Diese Tests halten die
umgekehrte Richtung fest — geschlossen, solange nichts anderes dransteht.
"""
import pytest

GESCHLOSSEN = (401, 403)

# Was zu keiner Zeit ohne Anmeldung gehen darf.
VERTRAULICH_LESEND = (
    "/api/leads/",
    "/api/leads/1",
    "/api/leads/1/profile",
    "/api/leads/export/csv",
    "/api/leads/customers",
    "/api/customers/",
    "/api/customers/1",
    "/api/usercards/",
)

VERAENDERND = (
    ("delete", "/api/leads/1"),
    ("patch", "/api/leads/1"),
    ("post", "/api/leads/1/kaltakquise"),
    ("post", "/api/leads/enrich/all"),
    ("post", "/api/leads/1/screenshot"),
    ("post", "/api/leads/1/pagespeed"),
    ("delete", "/api/usercards/1"),
    ("patch", "/api/customers/1"),
)


@pytest.mark.parametrize("pfad", VERTRAULICH_LESEND)
def test_ohne_anmeldung_gibt_es_keine_kundendaten(client, pfad):
    antwort = client.get(pfad, follow_redirects=True)

    assert antwort.status_code in GESCHLOSSEN, f"{pfad} → {antwort.status_code}"


@pytest.mark.parametrize("methode,pfad", VERAENDERND)
def test_ohne_anmeldung_laesst_sich_nichts_veraendern(client, methode, pfad):
    aufruf = getattr(client, methode)
    # DELETE nimmt beim Testclient keinen Rumpf entgegen.
    antwort = (aufruf(pfad, follow_redirects=True) if methode == "delete"
               else aufruf(pfad, json={}, follow_redirects=True))

    assert antwort.status_code in GESCHLOSSEN, f"{methode} {pfad} → {antwort.status_code}"


@pytest.mark.parametrize("pfad", VERTRAULICH_LESEND)
def test_mit_anmeldung_geht_es(client, auth_headers, pfad):
    """Die Sperre darf die Anwendung nicht mitnehmen."""
    antwort = client.get(pfad, headers=auth_headers, follow_redirects=True)

    assert antwort.status_code not in GESCHLOSSEN, f"{pfad} → {antwort.status_code}"


# ── Was öffentlich bleiben muss ───────────────────────────────────────

def test_der_kundenzugang_ueber_token_bleibt_offen():
    """Der Link aus der E-Mail trägt keinen Anmeldetoken — er ist der Nachweis.

    Ein 404 ist hier das richtige Ergebnis: Die Route antwortet, der Token
    existiert nur nicht.
    """
    # Der oeffentliche Router liegt seit dem 22.08.2026 in
    # `routers/leads_portal.py` (L-25) — zusammen mit dem Kundenweg ueber
    # Einmal-Token. In `leads.py` standen drei Router mit drei verschiedenen
    # Sperren nebeneinander; wer dort eine Route ergaenzte und den falschen
    # griff, oeffnete sie oder sperrte einen Kunden aus.
    from routers.leads_portal import public_router

    pfade = {r.path for r in public_router.routes}
    assert "/api/leads/portal/{token}" in pfade
    assert "/api/leads/public" in pfade


def test_der_geschuetzte_router_traegt_die_abhaengigkeit():
    """Damit eine neue Route nicht offen ist, weil jemand sie vergessen hat."""
    from routers.leads import router

    assert router.dependencies, "Lead-Router ohne Vorgabe-Anmeldung"


# ── Angemeldet heisst nicht berechtigt ────────────────────────────────
#
# Befund vom 18.08.2026: `require_innendienst` sperrt nur die Rolle `kunde`
# aus. Die Rechtematrix in `admin_settings.py` gibt `view_leads` und
# `view_projects` aber nur an **superadmin, admin und auditor** — die Rolle
# `nutzer` hat dieselben Rechte wie ein Kunde (Dashboard, Audits, PDF).
#
# Am laufenden Server nachgestellt: Ein Konto mit Rolle `nutzer` bekam auf
# `GET /api/leads/` eine **200** samt vollstaendigem Bestand. Dieselbe Luecke
# wie am 17.08. bei den Kundenzugaengen, nur eine Rolle weiter.
#
# Die Sperre fragt jetzt, **wer darf**, statt aufzuzaehlen, wer nicht darf:
# Eine spaeter erfundene Rolle ist damit erst einmal draussen.

NUTZER_EMAIL = "pytest-nutzer@kompagnon.local"
NUTZER_PASSWORT = "pytest-nutzer-passwort"


@pytest.fixture(scope="module")
def nutzer_headers(client, app):
    from auth import hash_password
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        vorhanden = db.query(User).filter(User.email == NUTZER_EMAIL).first()
        if not vorhanden:
            db.add(User(
                email=NUTZER_EMAIL,
                password_hash=hash_password(NUTZER_PASSWORT),
                first_name="Pytest", last_name="Nutzer",
                role="nutzer", is_active=True, is_verified=True,
            ))
            db.commit()
    finally:
        db.close()

    antwort = client.post("/api/auth/login",
                          json={"email": NUTZER_EMAIL, "password": NUTZER_PASSWORT})
    assert antwort.status_code == 200, antwort.text
    return {"Authorization": f"Bearer {antwort.json()['access_token']}"}


@pytest.mark.parametrize("pfad", ["/api/leads/", "/api/customers/"])
def test_die_rolle_nutzer_sieht_den_bestand_nicht(client, nutzer_headers, pfad):
    antwort = client.get(pfad, headers=nutzer_headers, follow_redirects=True)

    assert antwort.status_code == 403, (
        f"{pfad} -> {antwort.status_code}: Ein angemeldeter Nutzer bekommt "
        "Kundendaten, obwohl die Rechtematrix ihm view_leads nicht gibt."
    )


def test_die_sperre_zaehlt_auf_wer_darf(client):
    """Nicht wer nicht darf — sonst ist die naechste neue Rolle wieder drin."""
    import inspect

    from routers.auth_router import require_innendienst

    quelle = inspect.getsource(require_innendienst)
    assert "auditor" in quelle, "Die Sperre nennt die erlaubten Rollen nicht"


def test_auch_kein_einzelner_betrieb(client, nutzer_headers, kunde_user):
    """Am vorhandenen Datensatz geprueft — sonst waere ein 404 die Antwort,
    und der sagt nichts ueber die Berechtigung."""
    antwort = client.get(f"/api/leads/{kunde_user.lead_id}", headers=nutzer_headers)

    assert antwort.status_code == 403, f"-> {antwort.status_code}: {antwort.text[:120]}"
