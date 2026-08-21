"""L-28: Zwei Template-Router auf derselben Tabelle — jetzt einer.

`routers/templates.py` (`/api/templates`) und `routers/website_templates.py`
(`/api/website-templates`) arbeiteten beide auf `website_templates`. Drei
Endpunkte gab es doppelt (`GET /`, `PUT /{id}`, `DELETE /{id}`), zwei weitere
taten dasselbe unter anderem Namen (`/upload` gegen `/import`).

Gemessen am 21.08.2026: Das Frontend ruft **ausschliesslich** `/api/templates`
auf; `/api/website-templates` erreichte kein einziger Aufruf — weder im
Frontend, noch in den Browser-Tests, noch in der Dokumentation. Nur ein
Zugriffsschutz-Test kannte den Pfad.

Umgezogen sind deshalb die drei Endpunkte, die es **nur** dort gab:
`import-bulk` (Sammel-Import, den die Envato-Strecke aus L-16 brauchen wird),
`suggestions` und `{id}/preview`.

**Die Reihenfolge-Falle:** `GET /suggestions` muss **vor** `GET /{template_id}`
stehen. Sonst frisst der Platzhalter das Wort und FastAPI versucht,
„suggestions" als Zahl zu lesen. Genau so ist am 07.05. `/layout-presets`
hinter einem Catch-all verschwunden und lieferte drei Monate lang 404, ohne
dass es auffiel. Der erste Test hier misst das an der Antwort, nicht an der
Reihenfolge im Quelltext.
"""
import pytest


class TestReihenfolge:
    def test_suggestions_wird_nicht_vom_platzhalter_gefressen(self, client, auth_headers):
        # Act
        antwort = client.get("/api/templates/suggestions?gewerk=heizung",
                             headers=auth_headers)

        # Assert — 200 mit Inhalt, nicht 422 („suggestions ist keine Zahl")
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["gewerk"] == "heizung"

    def test_eine_zahl_landet_weiterhin_beim_platzhalter(self, client, auth_headers):
        # Act
        antwort = client.get("/api/templates/999999", headers=auth_headers)

        # Assert — 404 heisst: die Route hat gegriffen, die Zeile fehlt
        assert antwort.status_code == 404


class TestZusammenlegung:
    def test_der_zweite_router_ist_weg(self):
        """Er lag 365 Zeilen lang auf derselben Tabelle, und niemand rief ihn."""
        import pathlib

        wurzel = pathlib.Path(__file__).resolve().parent.parent
        assert not (wurzel / "routers" / "website_templates.py").exists()

    def test_kein_pfad_heisst_mehr_website_templates(self):
        import main

        assert not hasattr(main, "website_templates")

    @pytest.mark.parametrize("pfad", [
        "/api/templates/",
        "/api/templates/upload",
        "/api/templates/import-bulk",
        "/api/templates/suggestions",
        "/api/templates/{template_id}",
        "/api/templates/{template_id}/preview",
    ])
    def test_die_umgezogenen_endpunkte_sind_da(self, pfad):
        """Geprueft **am Router**, nicht an `app.routes`.

        Diese FastAPI-Fassung legt eingebundene Router als `_IncludedRouter`
        ab und flacht ihre Routen nicht auf — am 19.08. wurde deshalb beinahe
        ein Ladefehler gemeldet, den es nie gab. Siehe
        [[feedback-am-gegenstand-pruefen]].
        """
        from routers import templates

        # `r.path` traegt das Praefix bereits — es noch einmal davorzusetzen
        # ergab `/api/templates/api/templates/…` und einen Test, der aus dem
        # falschen Grund rot war.
        pfade = {r.path for r in templates.router.routes}
        assert pfad in pfade, sorted(pfade)
