"""Das Werkzeug ist kein offener Laden.

Befund vom 19.08.2026. Nach dem Fund am Webhook-Protokoll habe ich nicht
weitergeraten, sondern gezählt: **499 Routen durchgerufen, 90 antworteten ohne
Anmeldung.** 35 davon sollen das — Anmeldung, Widget, Kundenportal per Token,
die beiden Stripe-Webhooks, `/health`. Die übrigen 55 nicht.

Am Produktivsystem nachgemessen, ohne einen einzigen Anmeldeversuch:

    GET /api/dashboard/kpis            → 200, `average_margin_percent: 97.5`
    GET /api/dashboard/projects-by-phase → 200, Kundennamen samt Marge
    GET /api/audit/recent              → 200, die letzten Audits mit Firma
    GET /api/audit/lead/58             → 200, **187 KB** vollständige Audits
    GET /api/automations/jobs          → 200, die interne Jobliste
    POST /api/scheduler/restart        → 200 — er startete wirklich neu
    POST /api/scraper/run              → 200 — der Lauf begann wirklich

Es ist dieselbe Ursache wie am 14.08. bei der Leadliste und am 17.08. bei den
Kundenzugängen: Die Anmeldung hing an der einzelnen Route. `briefings.py` hatte
elf geschützte Routen und drei vergessene, `sitemap.py` achtzehn und eine. Wer
eine Route hinzufügt, öffnet sie — das ist die falsche Richtung, und sie lässt
sich nicht durch Sorgfalt beheben, nur durch eine Vorgabe am Router.

Diese Datei hält beide Richtungen fest: was zu sein hat, und was offen bleiben
muss. Der zweite Teil ist der wichtigere — er ist der Grund, warum hier nicht
einfach alles gesperrt wurde.
"""
import pytest

GESCHLOSSEN = (401, 403)

# ── Was ohne Anmeldung nicht zu haben sein darf ───────────────────────
#
# Reihenfolge wie gemessen. Ein Platzhalter wird mit `1` gefüllt; ob dahinter
# ein Datensatz liegt, ist für die Frage der Berechtigung ohne Belang — 404
# und 422 heißen beide „geprüft wurde nicht die Anmeldung, sondern der Inhalt".

# `/api/courses/*` stand hier bis zum 19.08.2026. Der Router ist mit der
# Zusammenführung der zwei Kurssysteme entfallen — siehe
# `test_kurse_zusammenfuehren.py`.
GESPERRT_LESEND = (
    "/api/agents/jobs/1",
    "/api/audit/recent",
    "/api/audit/lead/1",
    "/api/audit/1/angebot",
    "/api/audit/1/pdf",
    "/api/automations/jobs",
    "/api/branddesign/1",
    "/api/branddesign/1/guideline",
    "/api/branddesign/1/pdf",
    "/api/crawler/status",
    "/api/dashboard/alerts",
    "/api/dashboard/kpis",
    "/api/dashboard/projects-by-phase",
    "/api/designs/1",
    "/api/scheduler/status",
    "/api/scraper/chambers",
    "/api/scraper/health",
    "/api/scraper/status",
    "/api/sitemap/1/pdf",
    # Am 21.08. von `/api/website-templates/suggestions` hierher gezogen:
    # Die beiden Router lagen auf derselben Tabelle, und den zweiten rief
    # nichts auf (L-28).
    "/api/templates/suggestions",
)

GESPERRT_VERAENDERND = (
    ("post",   "/api/agents/1/content"),
    ("post",   "/api/agents/1/qa"),
    ("post",   "/api/agents/1/review"),
    ("post",   "/api/agents/1/seo"),
    ("delete", "/api/audit/1"),
    ("patch",  "/api/audit/1/link-lead"),
    ("post",   "/api/automations/test-email"),
    ("put",    "/api/branddesign/1"),
    ("post",   "/api/branddesign/1/analyze-screenshot"),
    ("post",   "/api/branddesign/1/check-ga"),
    ("put",    "/api/branddesign/1/guideline"),
    ("post",   "/api/branddesign/1/guideline/generate"),
    ("post",   "/api/branddesign/1/scrape"),
    ("post",   "/api/branddesign/1/suggest-fonts"),
    ("post",   "/api/branddesign/1/upload-pdf"),
    ("patch",  "/api/briefings/1"),
    ("post",   "/api/briefings/1/wettbewerbsanalyse"),
    ("post",   "/api/briefings/1/zielgruppenanalyse"),
    ("post",   "/api/designs/1"),
    ("post",   "/api/scheduler/restart"),
    ("post",   "/api/scraper/run"),
    ("post",   "/api/scraper/run-batch"),
    ("post",   "/api/scraper/schedule"),
    ("post",   "/api/templates/1/assign-lead"),
    ("post",   "/api/templates/1/assign-project"),
    ("patch",  "/api/tickets/1"),
)

# ── Was offen bleiben muss ────────────────────────────────────────────
#
# Jeder Eintrag hier ist eine Entscheidung, keine Auslassung. Wer eine dieser
# Routen sperrt, nimmt einem Menschen ohne Konto etwas weg, das er braucht.

OEFFENTLICH_MIT_GRUND = (
    ("post", "/api/audit/start",
     "Die öffentliche Landingpage (websprint-landing.html) startet damit das "
     "Gratis-Audit — der Interessent hat kein Konto und soll keines brauchen."),
    ("post", "/api/leads/public",
     "Dasselbe Formular, derselbe Grund."),
    ("get", "/api/academy/certificates/abc/verify",
     "Eine Urkunde prüft, wer sie vorgelegt bekommt. Ein Prüfer mit Konto "
     "wäre keine Prüfung."),
    ("get", "/health",
     "Der Deploy-Torwächter fragt hier, bevor es eine Anmeldung gibt."),
)


@pytest.mark.parametrize("pfad", GESPERRT_LESEND)
def test_ohne_anmeldung_gibt_das_werkzeug_nichts_heraus(client, pfad):
    # Act
    antwort = client.get(pfad, follow_redirects=True)

    # Assert
    assert antwort.status_code in GESCHLOSSEN, (
        f"GET {pfad} -> {antwort.status_code}"
    )


@pytest.mark.parametrize("methode,pfad", GESPERRT_VERAENDERND)
def test_ohne_anmeldung_handelt_das_werkzeug_nicht(client, methode, pfad):
    # Act
    aufruf = getattr(client, methode)
    antwort = (aufruf(pfad, follow_redirects=True) if methode == "delete"
               else aufruf(pfad, json={}, follow_redirects=True))

    # Assert
    assert antwort.status_code in GESCHLOSSEN, (
        f"{methode.upper()} {pfad} -> {antwort.status_code}"
    )


@pytest.mark.parametrize("pfad", GESPERRT_LESEND)
def test_mit_anmeldung_geht_es_weiterhin(client, auth_headers, pfad):
    """Die Sperre darf die Anwendung nicht mitnehmen."""
    # Act
    antwort = client.get(pfad, headers=auth_headers, follow_redirects=True)

    # Assert
    assert antwort.status_code not in GESCHLOSSEN, (
        f"GET {pfad} -> {antwort.status_code}: für den Innendienst zu"
    )


@pytest.mark.parametrize("methode,pfad,grund", OEFFENTLICH_MIT_GRUND)
def test_was_offen_bleiben_muss_bleibt_offen(client, methode, pfad, grund):
    """Mit der Methode fragen, die es wirklich gibt.

    Ein GET auf eine POST-Route sagt nichts über die Berechtigung — bei
    `/api/leads/public` fiel er sogar auf `GET /api/leads/{lead_id}` und
    holte sich dort ein 403 ab. Der erste Durchgang hat genau das gemessen.
    """
    # Act
    aufruf = getattr(client, methode)
    antwort = (aufruf(pfad, follow_redirects=True) if methode == "get"
               else aufruf(pfad, json={}, follow_redirects=True))

    # Assert — 404/405/422 sind in Ordnung, 401/403 nicht
    assert antwort.status_code not in GESCHLOSSEN, (
        f"{methode.upper()} {pfad} -> {antwort.status_code}. {grund}"
    )


# ── Die Richtung, nicht die Liste ─────────────────────────────────────

ROUTER_MIT_VORGABE = (
    "automations", "agents", "branddesign", "briefings",
    "crawler", "designs", "scraper", "sitemap", "templates",
)


@pytest.mark.parametrize("name", ROUTER_MIT_VORGABE)
def test_der_router_traegt_die_vorgabe_selbst(name):
    """Sonst ist die nächste neue Route wieder offen — genau so entstand das.

    Die Liste oben ist eine Momentaufnahme; sie kann eine morgen ergänzte
    Route nicht kennen. Diese Prüfung schon.
    """
    import importlib

    modul = importlib.import_module(f"routers.{name}")

    assert modul.router.dependencies, f"routers/{name}.py ohne Vorgabe-Anmeldung"
