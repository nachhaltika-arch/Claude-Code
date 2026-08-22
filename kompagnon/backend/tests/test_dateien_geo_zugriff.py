"""Dateien und GEO-Laeufe standen jedem Angemeldeten offen (L-67).

**Dritter Durchgang, 22.08.2026.** Nach `pages` und `content` bleiben die
naechsten beiden Bestaende, und der erste wiegt schwer:

* `GET /api/files/{lead_id}` — **alle Dateien eines fremden Betriebs
  auflisten**
* `GET /api/files/download/{file_id}` — und sie herunterladen
* `POST /api/files/upload/{lead_id}` — Dateien in einen fremden Betrieb legen

Dateien eines Handwerksbetriebs sind Vertraege, Angebote, Fotos, Logos. Sie
jedem Angemeldeten zu zeigen ist kein Anzeigefehler.

Der zweite Bestand sind die fuenf GEO-Routen — Analysen anstossen und
Dateien erzeugen lassen, alles auf fremden Projekten.

**Vor der Sperre gemessen.** Dateien: `ProjectFilesSection` (aus
`CustomerDetail` und `LeadProfile`), `OnboardingWizard` (Dashboard, von dem
Kunden weggeleitet werden), `GrapesEditor`, `WebsiteDesigner`,
`useGrapesAssetManager` — alles Innendienst. **Kein Aufruf aus
`KundenPortal.jsx` oder `pages/customer/`, keiner aus `CustomerDashboard`,
der Ansicht, auf der ein Kunde landet.** GEO: `GeoOptimizerStep` ueber
`KASSidebar` im `OnlineFertigEditor` (`roles={['admin','auditor']}`);
`ProzessFlow.jsx` bindet es ebenfalls ein, ist aber in keiner Seite mehr
eingehaengt.

**Nicht mitgesperrt: `/api/assistant/…`.** Das ist ein echter Kundenweg —
`AssistentPanel` haengt in `KundenPortal.jsx`. Dort ist die richtige Frage
nicht „welche Rolle", sondern „wessen Zeile".
"""
import pytest


WEGE = [
    ("get",  "/api/files/1", None),
    ("get",  "/api/files/download/1", None),
    ("get",  "/api/files/1/grapesjs-assets", None),
    ("get",  "/api/geo/1/result", None),
    ("post", "/api/geo/1/analyze", {}),
    ("post", "/api/geo/1/generate", {}),
    ("get",  "/api/geo/1/files", None),
    ("get",  "/api/geo/1/monitoring", None),
]


def _ruf(client, methode, pfad, rumpf, headers=None):
    zusatz = {"json": rumpf} if rumpf is not None else {}
    if headers:
        zusatz["headers"] = headers
    return getattr(client, methode)(pfad, **zusatz)


class TestDerKundeKommtNichtHeran:
    @pytest.mark.parametrize("methode,pfad,rumpf", WEGE)
    def test_kein_kunde(self, client, kunde_headers, methode, pfad, rumpf):
        antwort = _ruf(client, methode, pfad, rumpf, kunde_headers)

        assert antwort.status_code == 403, (
            f"{methode.upper()} {pfad} → {antwort.status_code}")

    @pytest.mark.parametrize("methode,pfad,rumpf", WEGE)
    def test_ohne_anmeldung_erst_recht_nicht(self, client, methode, pfad, rumpf):
        antwort = _ruf(client, methode, pfad, rumpf)

        assert antwort.status_code in (401, 403)


class TestDerKundenwegBleibtOffen:
    def test_der_assistent_bleibt_dem_kunden_erreichbar(self, client, kunde_headers):
        """`AssistentPanel` haengt in `KundenPortal.jsx`. Eine Rollensperre
        waere hier keine Haertung, sondern die Aussperrung der Zielgruppe."""
        antwort = client.get("/api/assistant/limits", headers=kunde_headers)

        assert antwort.status_code != 403, antwort.text[:200]


class TestDieSperreHaengtAmRouter:
    def test_beide_module_tragen_sie(self):
        import pathlib

        from routers import files, geo

        for modul in (files, geo):
            quelle = pathlib.Path(modul.__file__).read_text(encoding="utf-8")
            assert "Depends(require_innendienst)" in quelle, modul.__name__
