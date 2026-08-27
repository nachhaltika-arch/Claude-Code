# -*- coding: utf-8 -*-
"""
Der Endpunkt für die KI-Nennung hat einen Aufrufer (L-58 b).

**Der Befund vom 25.08.2026.** `POST /api/geo/{id}/ki-sichtbarkeit` gab es
seit dem 17.08.2026 — mit Messdienst, Speicherung, Verlauf und vier
Testdateien. **Aufgerufen hat ihn niemand:** Im Frontend stand kein `fetch`
darauf. Der Kasten im GEO-Schritt versprach dem Nutzer sogar, es werde
geprüft, ob die Seite „gefunden und zitiert" wird — geprüft wurde nur das
Erste.

Das ist die Fehlerklasse, die im Lagebild fünfmal steht: gebaut, nicht
angeschlossen. Sie fällt nicht auf, weil nichts kaputt ist — es passiert nur
nichts.

Dieser Test hält den Anschluss fest. Er prüft **Backend und Frontend
gemeinsam**, weil genau die Lücke dazwischen der Befund war.
"""
import pathlib
import re

import pytest

WURZEL = pathlib.Path(__file__).resolve().parents[3]
KOMPONENTE = (WURZEL / "kompagnon" / "frontend" / "src" / "components"
              / "GeoOptimizerStep.jsx")


def test_der_endpunkt_existiert():
    from main import app

    pfade = set(app.openapi()["paths"])
    assert "/api/geo/{project_id}/ki-sichtbarkeit" in pfade
    assert "/api/geo/{project_id}/ki-sichtbarkeit/verlauf" in pfade


@pytest.mark.parametrize("pfadstueck", ["ki-sichtbarkeit", "ki-sichtbarkeit/verlauf"])
def test_das_frontend_ruft_ihn_auf(pfadstueck):
    """Ohne Aufrufer ist der Endpunkt für den Nutzer nicht vorhanden."""
    assert KOMPONENTE.exists(), KOMPONENTE
    quelle = KOMPONENTE.read_text(encoding="utf-8")
    assert pfadstueck in quelle, (
        f"Kein Aufruf auf {pfadstueck} im GEO-Schritt — der Endpunkt wäre "
        "wieder gebaut und nicht angeschlossen.")


def test_ein_fehlender_schluessel_erscheint_nicht_als_null():
    """„Nicht erhoben" und „nicht gefunden" sind zwei verschiedene Nachrichten.

    Die zweite kostet den Betrieb Geld. Der Dienst darf für ein System, das
    nie gefragt wurde, keine Zahl liefern — und die Oberfläche darf keine
    daraus machen.
    """
    from services.ki_sichtbarkeit import verlaufseintrag

    befund = {"anbieter": {
        "chatgpt": {"collected": True, "genannt_bei": 2, "von": 3, "quote": .67},
        "perplexity": {"collected": False, "grund": "PERPLEXITY_API_KEY nicht gesetzt"},
    }}
    eintrag = verlaufseintrag(befund, "2026-08-25T12:00:00")

    assert eintrag["anbieter"]["chatgpt"]["genannt_bei"] == 2
    assert "perplexity" not in eintrag["anbieter"], (
        "ein nicht gefragtes System steht mit einer Zahl im Verlauf")
    assert eintrag["nicht_erhoben"] == ["perplexity"]

    quelle = KOMPONENTE.read_text(encoding="utf-8")
    assert "nicht erhoben" in quelle, (
        "die Oberfläche unterscheidet nicht zwischen nicht gefragt und nicht genannt")


def test_die_oberflaeche_haengt_keinen_score_daran():
    """Jeder Lauf kostet Geld — deshalb fließt er in keine Punktzahl ein.

    Diese Entscheidung steht so im Dienst und gehört David. Bis sie fällt,
    darf die Nennung nirgends in den GEO-Score einfließen.
    """
    quelle = KOMPONENTE.read_text(encoding="utf-8")
    nennungsblock = quelle.split("activeTab === 'nennung'")[1].split(
        "activeTab === 'monitoring'")[0]
    assert not re.search(r"geo_score|setScore|score\s*\+", nennungsblock), (
        "der Nennungsblock rechnet an einem Score mit")
