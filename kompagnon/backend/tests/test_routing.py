"""
Schutz gegen verdeckte Routen.

FastAPI prueft Routen in Registrierungsreihenfolge. Steht `/{slug}` vor
`/layout-presets`, faengt der Platzhalter die feste Route ab und die Anwendung
liefert 404 — ohne dass irgendwo ein Fehler auftaucht. Genau das ist am
2026-05-07 passiert und blieb drei Monate unbemerkt.

Dieser Test findet solche Faelle generisch, nicht nur den einen bekannten.
"""
import pytest


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
        for index, route in enumerate(app.routes)
        if getattr(route, "methods", None)
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


def test_app_registriert_erwartete_routenzahl(app):
    """Grober Wachhund gegen versehentlich entfernte Router."""
    assert len(app.routes) > 200
