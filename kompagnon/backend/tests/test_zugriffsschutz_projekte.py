"""Projekte sind nicht ohne Anmeldung zu haben.

Befund vom 17.08.2026: Der Projekt-Router trug — anders als der Lead-Router
seit dem 14.08. — keine Vorgabe-Anmeldung. Die Prüfung hing an der einzelnen
Route, und 19 von 60 Routen hatten sie nicht. Offen waren unter anderem:

    PUT    /api/projects/{id}          schreibt beliebige Spalten per Roh-SQL
    PATCH  /api/projects/{id}/phase    schaltet Phasen und löst Automatik aus
    POST   /api/projects/{id}/trigger  startet Automatisierungen
    POST   /api/projects/seed          legt Projekte aus Leads an
    GET    /api/projects/debug         Zeilenzahlen und Beispieldaten

Es ist dieselbe Bauart wie beim Lead-Router und wie in [[migration-trap-main-py]]:
richtig gebaut an vielen Stellen, und die vergessene Stelle kannte niemand.
Diese Tests halten die umgekehrte Richtung fest — geschlossen, solange nichts
anderes dransteht.
"""
import pytest

GESCHLOSSEN = (401, 403)

# Lesende Routen, die ohne Anmeldung nichts preisgeben dürfen.
VERTRAULICH_LESEND = (
    "/api/projects/",
    "/api/projects/debug",
    "/api/projects/1",
    "/api/projects/1/checklist",
    "/api/projects/1/margin",
    "/api/projects/1/qa/result",
    # `/api/projects/1/scrape-content` stand hier bis zum 26.08.2026. Die
    # Route ist entfernt (Entscheidung David: „der crawler ist der richtige,
    # den anderen weg") — sie stehen zu lassen hiesse, eine 404 als
    # Zugriffsschutz zu feiern.
    "/api/projects/1/versions/1/preview",
)

# Verändernde Routen. Mehrere davon kosten Geld (Scrape, Netlify, KI) oder
# lösen Kundenmails aus — sie werden hier nur unangemeldet aufgerufen.
VERAENDERND = (
    ("put",   "/api/projects/1"),
    ("patch", "/api/projects/1/phase"),
    ("patch", "/api/projects/1/checklist/domain"),
    ("post",  "/api/projects/seed"),
    ("post",  "/api/projects/1/time"),
    ("post",  "/api/projects/1/trigger"),
    ("post",  "/api/projects/from-lead/1"),
    # `/api/projects/1/scrape` stand hier bis zum 01.09.2026. Wie schon
    # `scrape-content` am 26.08. ist die Route entfernt (L-105): Sie war der
    # aermere von zwei Branddesign-Laeufen, und die Werkstatt ruft den
    # anderen — `POST /api/branddesign/{lead_id}/scrape`. Eine 404 als
    # Zugriffsschutz zu feiern waere dieselbe Selbsttaeuschung wie damals.
    ("post",  "/api/projects/1/hosting-scan"),
    ("post",  "/api/projects/1/domain-check"),
    ("post",  "/api/projects/1/qa/run"),
)

# Harmlos genug, um sie angemeldet wirklich aufzurufen: reines Lesen,
# kein Netz, keine Kosten.
UNGEFAEHRLICH_LESEND = (
    "/api/projects/",
    "/api/projects/1",
    "/api/projects/1/checklist",
    "/api/projects/1/margin",
)


@pytest.mark.parametrize("pfad", VERTRAULICH_LESEND)
def test_ohne_anmeldung_gibt_es_keine_projektdaten(client, pfad):
    antwort = client.get(pfad, follow_redirects=True)

    assert antwort.status_code in GESCHLOSSEN, f"{pfad} → {antwort.status_code}"


@pytest.mark.parametrize("methode,pfad", VERAENDERND)
def test_ohne_anmeldung_laesst_sich_nichts_veraendern(client, methode, pfad):
    aufruf = getattr(client, methode)

    antwort = aufruf(pfad, json={}, follow_redirects=True)

    assert antwort.status_code in GESCHLOSSEN, f"{methode} {pfad} → {antwort.status_code}"


@pytest.mark.parametrize("pfad", UNGEFAEHRLICH_LESEND)
def test_mit_anmeldung_geht_es(client, auth_headers, pfad):
    """Die Sperre darf die Anwendung nicht mitnehmen."""
    antwort = client.get(pfad, headers=auth_headers, follow_redirects=True)

    assert antwort.status_code not in GESCHLOSSEN, f"{pfad} → {antwort.status_code}"


# ── Was öffentlich bleiben muss ───────────────────────────────────────

def test_die_freigabe_ueber_token_bleibt_offen(client):
    """Der Freigabe-Link aus der Kundenmail trägt keinen Anmeldetoken.

    Ein 404 ist hier das richtige Ergebnis: Die Route antwortet, den Token
    gibt es nur nicht.
    """
    antwort = client.get("/api/projects/approve-content/gibtesnicht")

    assert antwort.status_code == 404


def test_die_freigabe_liegt_im_oeffentlichen_router():
    from routers.projects import public_router

    pfade = {r.path for r in public_router.routes}
    assert "/api/projects/approve-content/{token}" in pfade


def test_der_geschuetzte_router_traegt_die_abhaengigkeit():
    """Damit eine neue Route nicht offen ist, weil jemand sie vergessen hat."""
    from routers.projects import router

    assert router.dependencies, "Projekt-Router ohne Vorgabe-Anmeldung"


# Die einzigen Projekt- und Lead-Routen, die ohne Anmeldung erreichbar sein
# dürfen. Wächst diese Liste, war es eine Entscheidung — kein Versehen.
OEFFENTLICH_ERLAUBT = {
    "/api/projects/approve-content/{token}",
    "/api/leads/public",
    "/api/leads/portal/{token}",
    "/api/leads/portal/{token}/verify",
    "/api/leads/portal/{token}/complete-onboarding",
}

# `require_auditor` stand hier bis zum 27.08.2026 und hing an keiner Route
# (L-12); mit der Rolle ist die Sperre weg. Ein Name in dieser Liste, den es
# nicht gibt, ist nicht harmlos: Er laesst die Liste vollstaendiger aussehen,
# als sie ist.
ANMELDEPRUEFUNGEN = (
    "require_admin", "require_superadmin",
    "require_any_auth", "require_innendienst", "require_kunde",
    "get_current_user",
)


def alle_routen(behaelter):
    """Läuft durch eingebundene Router hindurch.

    `app.routes` enthält in dieser FastAPI-Version nicht die einzelnen
    Routen, sondern die eingebundenen Router als eigene Objekte.
    """
    for eintrag in getattr(behaelter, "routes", []):
        eingebunden = getattr(eintrag, "original_router", None)
        if eingebunden is not None:
            yield from alle_routen(eingebunden)
        else:
            yield eintrag


def namen_der_abhaengigkeiten(dependant) -> set:
    """Alle Abhängigkeiten einer Route, auch die verschachtelten.

    `require_innendienst` hängt selbst an `get_current_user` — beide Ebenen
    zählen.
    """
    namen = set()
    for teil in getattr(dependant, "dependencies", []):
        aufruf = getattr(teil, "call", None)
        if aufruf is not None:
            namen.add(getattr(aufruf, "__name__", type(aufruf).__name__))
        namen |= namen_der_abhaengigkeiten(teil)
    return namen


def test_keine_einzige_route_haengt_frei(app):
    """Der eigentliche Befund, als Netz gespannt.

    Nicht "der Router trägt eine Abhängigkeit", sondern: Keine einzige Route
    unter /api/projects und /api/leads kommt ohne Anmeldeprüfung aus — egal
    ob sie an der Route hängt oder am Router. Wer morgen eine Route
    hinzufügt und es vergisst, bricht diesen Test.
    """
    geprueft = 0
    offen = []
    for route in alle_routen(app):
        pfad = getattr(route, "path", "")
        if not pfad.startswith(("/api/projects", "/api/leads")):
            continue
        if pfad in OEFFENTLICH_ERLAUBT:
            continue
        if not hasattr(route, "dependant"):
            continue

        geprueft += 1
        if not namen_der_abhaengigkeiten(route.dependant) & set(ANMELDEPRUEFUNGEN):
            offen.append(f"{sorted(route.methods)} {pfad}")

    # Sonst geht der Test durch, weil er nichts gefunden hat.
    assert geprueft > 50, f"Nur {geprueft} Routen geprüft — läuft der Durchlauf?"
    assert not offen, "Routen ohne Anmeldeprüfung:\n" + "\n".join(sorted(offen))
