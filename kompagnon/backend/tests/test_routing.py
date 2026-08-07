"""
Schutz gegen verdeckte Routen.

FastAPI prueft Routen in Registrierungsreihenfolge. Steht `/{slug}` vor
`/layout-presets`, faengt der Platzhalter die feste Route ab und die Anwendung
liefert 404 — ohne dass irgendwo ein Fehler auftaucht. Genau das ist am
2026-05-07 passiert und blieb drei Monate unbemerkt.

Dieser Test findet solche Faelle generisch, nicht nur den einen bekannten.
"""
import pytest


def _routen(app) -> list:
    """
    (Methode, Pfad) aller Endpunkte in Registrierungsreihenfolge.

    Quelle ist bewusst das OpenAPI-Schema und nicht `app.routes`: Wie Starlette
    Routen intern ablegt, aendert sich zwischen Versionen. Mit Starlette 1.0
    lieferte `app.routes` 470 Eintraege, mit 1.4 nur noch 63 — die per
    include_router eingebundenen Routen fehlten dort komplett, und der Test
    haette in der CI genau die Faelle uebersehen, die er finden soll.
    Das Schema liefert in beiden Faellen alle 369 Pfade, in stabiler Reihenfolge.
    """
    schema = app.openapi()
    return [
        (methode.upper(), pfad)
        for pfad, operationen in schema["paths"].items()
        for methode in operationen
        if methode.lower() in {"get", "post", "put", "patch", "delete"}
    ]


def _segments(path: str) -> list:
    return [s for s in path.split("/") if s]


def _is_placeholder(segment: str) -> bool:
    return segment.startswith("{") and segment.endswith("}")


def _shadows(earlier: str, later: str) -> bool:
    """Faengt die frueher registrierte Route die spaetere ab?"""
    a, b = _segments(earlier), _segments(later)
    if len(a) != len(b):
        return False

    has_placeholder_over_literal = False
    for seg_a, seg_b in zip(a, b):
        if seg_a == seg_b:
            continue
        if _is_placeholder(seg_a) and not _is_placeholder(seg_b):
            has_placeholder_over_literal = True
            continue
        return False

    return has_placeholder_over_literal


def test_keine_route_wird_von_einem_platzhalter_verdeckt(app):
    routen = _routen(app)

    verdeckt = []
    for index_a, (method_a, path_a) in enumerate(routen):
        for method_b, path_b in routen[index_a + 1:]:
            if method_a != method_b:
                continue
            if _shadows(path_a, path_b):
                verdeckt.append(f"{method_a} {path_b} wird von {path_a} verdeckt")

    assert not verdeckt, (
        "Diese Routen sind nicht erreichbar — die Platzhalter-Route muss NACH "
        "der festen Route registriert werden:\n  " + "\n  ".join(sorted(set(verdeckt)))
    )


def test_layout_presets_ist_erreichbar(client, auth_headers):
    """Der konkrete Fall von 2026-05-07: musste 404 liefern, muss jetzt 200."""
    response = client.get("/api/components/layout-presets", headers=auth_headers)

    assert response.status_code == 200
    presets = response.json()
    assert isinstance(presets, list)
    assert len(presets) > 0, "Layout-Presets sind leer — der Selector bliebe unsichtbar"
    assert {"id", "category"} <= set(presets[0])


@pytest.mark.parametrize("methode,pfad", [
    ("GET",  "/health"),
    ("POST", "/api/auth/login"),
    ("GET",  "/api/components"),
    ("GET",  "/api/components/layout-presets"),
    ("POST", "/api/leads/public"),
    ("POST", "/api/messages/send-email"),
    ("GET",  "/api/projects/"),
    ("GET",  "/api/briefings/{lead_id}"),
])
def test_wesentliche_endpunkte_sind_registriert(app, methode, pfad):
    """
    Wachhund gegen versehentlich entfernte oder umbenannte Router.

    Bewusst eine Liste konkreter Endpunkte statt einer Mindestanzahl: Die
    Routenzahl haengt von der Starlette-Version ab und war deshalb als
    Kriterium unbrauchbar.
    """
    assert (methode, pfad) in set(_routen(app)), f"{methode} {pfad} ist nicht registriert"
