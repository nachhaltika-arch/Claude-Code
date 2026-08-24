"""
Schutz gegen verdeckte Routen.

FastAPI prueft Routen in Registrierungsreihenfolge. Steht `/{slug}` vor
`/layout-presets`, faengt der Platzhalter die feste Route ab und die Anwendung
liefert 404 — ohne dass irgendwo ein Fehler auftaucht. Genau das ist am
2026-05-07 passiert und blieb drei Monate unbemerkt.

Dieser Test findet solche Faelle generisch, nicht nur den einen bekannten.
"""
import pytest


METHODEN = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _routen(app) -> list:
    """
    (Methode, Pfad) aller Endpunkte in **echter** Registrierungsreihenfolge.

    **Warum nicht mehr das OpenAPI-Schema (L-96, 24.08.2026).** Das Schema
    gruppiert nach *Pfad*: Alle Methoden eines Pfads erben dessen eine
    Position. Wandert eine einzelne Methode eines Platzhalter-Pfads nach vorn
    — etwa `DELETE /{project_id}` in ein frueher geladenes Modul —, ruecken
    **alle** Methoden dieses Pfads mit, auch die, die in Wirklichkeit spaeter
    registriert sind. Der Test meldete daraufhin `GET /api/projects/debug` als
    verdeckt, obwohl es erreichbar war. Ein Waechter, der falsch alarmiert,
    wird abgeschaltet — und faengt dann auch die echten Faelle nicht mehr.
    Umgekehrt kann dieselbe Blindheit einen echten Fall verbergen.

    **Warum `app.routes` frueher untauglich schien — und es nicht ist.** Der
    alte Docstring notierte: Starlette 1.0 lieferte 470 Eintraege, 1.4 nur
    noch 63. Die Beobachtung stimmt, die Schlussfolgerung war falsch. Ab 1.4
    legt Starlette eingebundene Router **verschachtelt** ab, als
    `_IncludedRouter` mit `.original_router`; die Routen sind nicht weg,
    sondern eine Ebene tiefer. Am 24.08.2026 nachgemessen: 82 Eintraege oben,
    daraus rekursiv **476** Paare — die 472 des Schemas **vollstaendig**, plus
    FastAPIs eigene vier (`/docs`, `/redoc`, `/openapi.json`,
    `/docs/oauth2-redirect`), die auch wirklich registriert sind.

    Das Praefix muss dabei mitlaufen: Eine Route (`generate-mockup`) traegt es
    nicht im eigenen Pfad, sondern nur im Einbindungs-Kontext. Ohne die
    Sammlung fehlte genau sie in der Deckung.
    """
    return list(_flach(app.routes))


def _flach(routen, praefix: str = ""):
    """Steigt in eingebundene Router ab und sammelt dabei das Präfix ein."""
    for route in routen:
        eingebunden = getattr(route, "original_router", None)
        if eingebunden is not None:
            kontext = getattr(route, "include_context", None)
            yield from _flach(
                eingebunden.routes,
                praefix + (getattr(kontext, "prefix", "") or ""),
            )
            continue

        pfad = getattr(route, "path", None)
        methoden = getattr(route, "methods", None)
        if not pfad or not methoden:
            continue
        for methode in sorted(methoden & METHODEN):
            yield (methode, praefix + pfad)


def verdeckte_routen(routen: list) -> list:
    """Welche Route wird von einer frueher registrierten abgefangen?

    Eigene Funktion, damit sie an einer erfundenen Liste prüfbar ist — der
    alte Wächter war nur gegen die echte Anwendung zu prüfen, und deshalb ist
    nie aufgefallen, dass er den Methodenfall nicht sieht.
    """
    verdeckt = []
    for index_a, (method_a, path_a) in enumerate(routen):
        for method_b, path_b in routen[index_a + 1:]:
            if method_a != method_b:
                continue
            if _shadows(path_a, path_b):
                verdeckt.append(f"{method_a} {path_b} wird von {path_a} verdeckt")
    return verdeckt


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


def test_die_reihenfolge_ist_ueberhaupt_vollstaendig(app):
    """Ein Wächter, der die halbe Anwendung nicht sieht, ist grün und blind.

    Genau das war der Zustand bis zum 24.08.2026 — nur andersherum: Die
    Reihenfolge war vollständig, aber pro *Pfad* statt pro (Methode, Pfad).
    Diese Prüfung hält fest, dass der neue Weg wirklich alles findet, was das
    Schema kennt. Bricht Starlette die Struktur erneut, wird das hier rot und
    nicht stillschweigend übersehen.
    """
    # Arrange
    aus_schema = {
        (methode.upper(), pfad)
        for pfad, operationen in app.openapi()["paths"].items()
        for methode in operationen
        if methode.upper() in METHODEN
    }

    # Act
    gefunden = set(_routen(app))

    # Assert
    assert aus_schema - gefunden == set(), (
        "Diese Endpunkte kennt das Schema, die Reihenfolge aber nicht — "
        f"der Wächter wäre für sie blind: {sorted(aus_schema - gefunden)[:10]}"
    )


def test_der_methodenfall_wird_erkannt():
    """Der Fall, den die Schema-Reihenfolge nicht sehen konnte (L-96).

    Erfundene Liste statt echter Anwendung: `DELETE /x/{id}` wird **vor**
    `GET /x/fest` registriert, `GET /x/{id}` **danach**. Nach Pfad gruppiert
    sähe `/x/{id}` früh aus und `GET /x/fest` fälschlich verdeckt; nach
    (Methode, Pfad) gemessen ist nichts verdeckt.
    """
    # Arrange
    routen = [
        ("DELETE", "/x/{id}"),
        ("GET", "/x/fest"),
        ("GET", "/x/{id}"),
    ]

    # Act & Assert — kein Fehlalarm
    assert verdeckte_routen(routen) == []

    # Und andersherum: steht der Platzhalter derselben Methode davor,
    # ist es ein echter Fund.
    assert verdeckte_routen([("GET", "/x/{id}"), ("GET", "/x/fest")]) == [
        "GET /x/fest wird von /x/{id} verdeckt"
    ]


def test_der_durchlauf_bildet_die_echte_reihenfolge_ab():
    """An einer gebauten App geprüft, nicht am Schema abgelesen.

    Die Bauart ist die der Anwendung: zwei `APIRouter` mit demselben Präfix,
    per `include_router` eingebunden — also genau die Verschachtelung, die
    Starlette 1.4 als `_IncludedRouter` ablegt und die der alte Wächter nicht
    durchdringen konnte.
    """
    from fastapi import APIRouter, FastAPI

    # Arrange
    mit_platzhalter = APIRouter(prefix="/api/dinge")

    @mit_platzhalter.get("/{ding_id}")
    def _platzhalter(ding_id: str):
        return {}

    mit_fester_route = APIRouter(prefix="/api/dinge")

    @mit_fester_route.get("/uebersicht")
    def _feste_route():
        return {}

    falsch_herum = FastAPI()
    falsch_herum.include_router(mit_platzhalter)   # Platzhalter zuerst
    falsch_herum.include_router(mit_fester_route)

    richtig_herum = FastAPI()
    richtig_herum.include_router(mit_fester_route)  # feste Route zuerst
    richtig_herum.include_router(mit_platzhalter)

    # Act & Assert
    assert verdeckte_routen(_routen(falsch_herum)) == [
        "GET /api/dinge/uebersicht wird von /api/dinge/{ding_id} verdeckt"
    ]
    assert verdeckte_routen(_routen(richtig_herum)) == []


def test_keine_route_wird_von_einem_platzhalter_verdeckt(app):
    verdeckt = verdeckte_routen(_routen(app))

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
