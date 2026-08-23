"""Drei Router unter `/api/projects` liessen jeden Angemeldeten an jedes Projekt.

Gefunden am 21.08.2026 beim Auftrennen der zweiten Nahtstelle aus
`docs/module-karte.md`. Vier Router bedienen `/api/projects`:

    projects.router                  61 Routen   require_innendienst   ✓
    component_library.wireframe_router 8 Routen   nur angemeldet       ✗
    content_scraper_router.router      4 Routen   nur angemeldet       ✗
    export.router                      1 Route    nur angemeldet       ✗

Die dreizehn Routen der unteren drei trugen `require_any_auth` und **keine
Zeilenpruefung**: Sie holen das Projekt per `project_id` und antworten. Kunden
haben Konten — ein angemeldeter Kunde konnte damit

  * die fertige Website **jedes** Projekts als ZIP herunterladen,
  * den Wireframe jedes Projekts lesen **und ueberschreiben**,
  * auf jedem Projekt einen Inhalts-Lauf starten und dessen Ergebnis lesen.

Dieselbe Bauart wie L-66 (`cms_connect`), nur dreizehnmal statt viermal — und
gefunden, weil dieselbe Frage ein zweites Mal gestellt wurde.

**Kein Kundenbildschirm braucht sie.** Alle Aufrufer haengen an
`roles={['admin', 'auditor']}`; `export-zip` hat ueberhaupt keinen Aufrufer.
Die Sperre stand also wieder in der Oberflaeche statt am Endpunkt.
"""
import pytest


GESCHUETZT = (
    ("get",  "/api/projects/1/export-zip"),
    ("get",  "/api/projects/1/wireframe"),
    ("post", "/api/projects/1/wireframe"),
    ("post", "/api/projects/1/wireframe/generate"),
    ("post", "/api/projects/1/wireframe/variant"),
    ("post", "/api/projects/1/wireframe/compose"),
    ("post", "/api/projects/1/scrape-full"),
    ("get",  "/api/projects/1/scrape-full"),
    ("get",  "/api/projects/1/scrape-status"),
    ("get",  "/api/projects/1/scraped-content"),
)


def _ruf(client, verb, pfad, headers=None):
    fn = getattr(client, verb)
    return fn(pfad, headers=headers) if verb == "get" else fn(pfad, headers=headers, json={})


@pytest.mark.parametrize("verb,pfad", GESCHUETZT)
def test_ein_kunde_kommt_an_kein_fremdes_projekt(client, kunde_headers, verb, pfad):
    # Act
    antwort = _ruf(client, verb, pfad, kunde_headers)

    # Assert — 200 und 422 waeren beide falsch: Bei 422 war er durch die
    # Sperre und stand schon bei der Feldpruefung.
    assert antwort.status_code in (401, 403, 404), (
        f"{verb.upper()} {pfad} antwortete {antwort.status_code} — "
        "ein Kunde ist an einem fremden Projekt."
    )


@pytest.mark.parametrize("verb,pfad", GESCHUETZT)
def test_ohne_anmeldung_erst_recht_nicht(client, verb, pfad):
    antwort = _ruf(client, verb, pfad)
    assert antwort.status_code in (401, 403, 404)


def test_der_innendienst_kommt_weiterhin_durch(client, auth_headers):
    """Die Sperre darf nicht den treffen, der den Editor bedient.

    404 ist die richtige Antwort fuer ein Projekt, das es nicht gibt — sie
    beweist, dass die Anfrage **durch** die Sperre bis zur Datenbank kam.
    """
    antwort = client.get("/api/projects/999999/wireframe", headers=auth_headers)
    assert antwort.status_code == 404, antwort.text[:200]


def test_alle_vier_router_der_naht_tragen_eine_vorgabe():
    """Am Router, nicht an der Route — genau diese Bauart hat am 19.08.
    55 offene Routen erzeugt (L-51)."""
    from routers import (component_library_wireframe, content_scraper_router,
                         export, projects)

    fuer_pruefung = (
        ("projects.router", projects.router),
        # Seit dem 22.08.2026 in einer eigenen Datei (L-25) — die Sperre
        # ist mitgewandert, dieser Test haelt sie fest.
        ("component_library_wireframe.wireframe_router",
         component_library_wireframe.wireframe_router),
        ("content_scraper_router.router", content_scraper_router.router),
        ("export.router", export.router),
    )
    ohne = []
    for name, router in fuer_pruefung:
        namen = [getattr(d.dependency, "__name__", "?") for d in router.dependencies]
        if "require_innendienst" not in namen:
            ohne.append(f"{name}: {namen}")

    assert ohne == [], ohne
