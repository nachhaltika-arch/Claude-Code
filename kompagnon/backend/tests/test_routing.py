"""
Schutz gegen verdeckte Routen.

FastAPI prueft Routen in Registrierungsreihenfolge. Steht `/{slug}` vor
`/layout-presets`, faengt der Platzhalter die feste Route ab und die Anwendung
liefert 404 — ohne dass irgendwo ein Fehler auftaucht. Genau das ist am
2026-05-07 passiert und blieb drei Monate unbemerkt.

Dieser Test findet solche Faelle generisch, nicht nur den einen bekannten.
"""
import pytest


def _iter_routes(node):
    """
    Alle Routen in Registrierungsreihenfolge — auch verschachtelte.

    Je nach Starlette-Version liegen Routen flach in `app.routes` oder in
    untergeordneten Routern. Ohne rekursives Durchlaufen sieht der Test in der
    einen Umgebung 470 Routen und in der anderen 63 — und uebersieht dort
    genau die Faelle, die er finden soll.
    """
    for route in getattr(node, "routes", []):
        if hasattr(route, "path") and getattr(route, "methods", None):
            yield route
        if hasattr(route, "routes"):
            yield from _iter_routes(route)


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
    routes = [
        (route.path, method, index)
        for index, route in enumerate(_iter_routes(app))
        for method in route.methods
    ]

    verdeckt = []
    for path_a, method_a, index_a in routes:
        for path_b, method_b, index_b in routes:
            if index_b <= index_a or method_a != method_b:
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
    vorhanden = {
        (m, route.path)
        for route in _iter_routes(app)
        for m in route.methods
    }

    assert (methode, pfad) in vorhanden, f"{methode} {pfad} ist nicht registriert"
