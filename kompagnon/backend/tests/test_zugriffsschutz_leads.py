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
# Befund vom 18.08.2026: `require_innendienst` sperrte nur die Rolle `kunde`
# aus. Die Rechtematrix gab `view_leads` aber nur an superadmin, admin und
# auditor — die damalige Rolle `nutzer` hatte dieselben Rechte wie ein Kunde
# (Dashboard, Audits, PDF). Am laufenden Server nachgestellt: Ein Konto mit
# Rolle `nutzer` bekam auf `GET /api/leads/` eine **200** samt vollstaendigem
# Bestand. Dieselbe Luecke wie am 17.08. bei den Kundenzugaengen, eine Rolle
# weiter. Die Sperre fragt seither, **wer darf**, statt aufzuzaehlen, wer
# nicht darf.
#
# **Umgeschrieben am 27.08.2026.** Die Rolle `nutzer` gibt es nicht mehr; sie
# ist mit `auditor` zu `mitarbeiter` zusammengelegt. Damit waere der alte Test
# sinnlos geworden — die neue Rolle *darf* den Bestand sehen.
#
# Geprueft wird jetzt die Eigenschaft, um die es damals ging, und zwar
# schaerfer: **Die Sperre liest die Rechtetabelle, nicht den Rollennamen.**
# Derselbe Mitarbeiter kommt mit dem Recht durch und ohne es nicht. Ein Test,
# der nur den Entzug prueft, waere auch dann gruen, wenn die Route fuer alle
# geschlossen waere.


def _view_leads_setzen(rolle: str, erlaubt: bool):
    from database import RolePermission, SessionLocal

    db = SessionLocal()
    try:
        eintrag = (db.query(RolePermission)
                     .filter(RolePermission.role == rolle,
                             RolePermission.permission == "view_leads")
                     .first())
        if eintrag:
            eintrag.is_allowed = erlaubt
        else:
            db.add(RolePermission(role=rolle, permission="view_leads",
                                  is_allowed=erlaubt))
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def rechte_zuruecksetzen():
    yield
    from database import RolePermission, SessionLocal

    db = SessionLocal()
    try:
        db.query(RolePermission).delete()
        db.commit()
    finally:
        db.close()


@pytest.mark.parametrize("pfad", ["/api/leads/", "/api/customers/"])
def test_mit_dem_recht_kommt_der_mitarbeiter_an_den_bestand(
        client, mitarbeiter_headers, pfad):
    """Die positive Haelfte. Ohne sie sagt die negative nichts."""
    antwort = client.get(pfad, headers=mitarbeiter_headers,
                         follow_redirects=True)

    assert antwort.status_code == 200, antwort.text[:200]


@pytest.mark.parametrize("pfad", ["/api/leads/", "/api/customers/"])
def test_ohne_das_recht_sieht_er_ihn_nicht(
        client, mitarbeiter_headers, rechte_zuruecksetzen, pfad):
    _view_leads_setzen("mitarbeiter", False)

    antwort = client.get(pfad, headers=mitarbeiter_headers,
                         follow_redirects=True)

    assert antwort.status_code == 403, (
        f"{pfad} -> {antwort.status_code}: Ein Angemeldeter bekommt "
        "Kundendaten, obwohl die Rechtematrix ihm view_leads entzogen hat."
    )


def test_dem_admin_kann_man_es_nicht_nehmen(client, auth_headers,
                                            rechte_zuruecksetzen):
    """Der Boden unter der Rechtetabelle.

    Ohne ihn koennte ein einziger Haken den letzten aussperren, der ihn
    wieder wegnehmen koennte.
    """
    _view_leads_setzen("admin", False)

    antwort = client.get("/api/leads/", headers=auth_headers,
                         follow_redirects=True)

    assert antwort.status_code == 200, antwort.text[:200]


def test_auch_kein_einzelner_betrieb(client, mitarbeiter_headers, kunde_user,
                                     rechte_zuruecksetzen):
    """Am vorhandenen Datensatz geprueft — sonst waere ein 404 die Antwort,
    und der sagt nichts ueber die Berechtigung."""
    _view_leads_setzen("mitarbeiter", False)

    antwort = client.get(f"/api/leads/{kunde_user.lead_id}",
                         headers=mitarbeiter_headers)

    assert antwort.status_code == 403, f"-> {antwort.status_code}: {antwort.text[:120]}"
