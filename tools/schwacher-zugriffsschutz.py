#!/usr/bin/env python3
"""Welche Routen antworten jedem Angemeldeten? (L-67)

**Warum an der geladenen Anwendung und nicht am Text.** Eine Sperre kann an
zwei Stellen haengen: in der Signatur der Funktion (`user=Depends(...)`) oder
am Router (`APIRouter(dependencies=[...])`). Wer nur die Funktionskoepfe
liest, sieht die halbe Wahrheit — genau das ist am 22.08.2026 einmal
passiert: Alle sechs Wireframe-Routen tragen `require_any_auth` in der
Signatur und sind trotzdem dicht, weil ihr Router `require_innendienst`
traegt (L-87).

FastAPI loest beides in `route.dependant` auf. Gezaehlt wird deshalb dort:
Eine Route gilt als **schwach geschuetzt**, wenn unter ihren aufgeloesten
Abhaengigkeiten eine schwache vorkommt und **keine** starke.

Aufruf im Backend-Verzeichnis:

    python tools/schwacher-zugriffsschutz.py
"""
import os
import sys
from collections import defaultdict

# Das Backend liegt neben diesem Werkzeug, nicht darueber — `main` steht in
# `kompagnon/backend`, und von dort muss der Aufruf kommen.
_WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_WURZEL, "kompagnon", "backend"))

#: Diese sagen nur „irgendjemand ist angemeldet".
SCHWACH = {"require_any_auth", "get_current_user", "optional_auth"}

#: Diese sagen, **wer**. Eine davon genuegt, egal auf welcher Ebene.
STARK = {"require_innendienst", "require_admin", "require_superadmin",
         "verlangt_recht", "require_auditor"}


def namen(dependant, gesehen=None) -> set:
    """Alle Abhaengigkeitsnamen einer Route — Router-Ebene eingeschlossen."""
    gesehen = gesehen or set()
    gefunden = set()
    for unter in dependant.dependencies:
        aufruf = getattr(unter, "call", None)
        name = getattr(aufruf, "__name__", None)
        if name:
            # `verlangt_recht("x")` liefert eine innere Funktion; ihr
            # `__qualname__` traegt den aeusseren Namen.
            gefunden.add(name)
            qual = getattr(aufruf, "__qualname__", "")
            if "." in qual:
                gefunden.add(qual.split(".")[0])
        if id(unter) not in gesehen:
            gesehen.add(id(unter))
            gefunden |= namen(unter, gesehen)
    return gefunden


def alle_routen(traeger, tiefe=0):
    """Jede Route, auch die in eingebundenen Routern.

    **Die Falle.** `app.routes` liefert unter dieser Starlette-Fassung 71
    Eintraege, waehrend `app.openapi()["paths"]` 391 kennt: 58 davon sind
    `_IncludedRouter`, also eingebundene Router, die ihre Routen selbst
    fuehren. Wer `app.routes` zaehlt, misst ein Sechstel und haelt es fuer
    das Ganze — dieselbe Falle ist am 22.08.2026 schon einmal zugeschnappt.

    `app.openapi()` waere hier keine Hilfe: Es kennt die Pfade, aber nicht
    die aufgeloesten Abhaengigkeiten. Also rekursiv durch die Traeger.
    """
    if tiefe > 6:
        return
    for eintrag in getattr(traeger, "routes", []):
        if hasattr(eintrag, "dependant"):
            yield eintrag
            continue
        # `_IncludedRouter` fuehrt seine Routen unter `original_router`. Die
        # dortigen `dependant` tragen die Router-Abhaengigkeiten bereits —
        # nachgeprueft an `/api/projects/{project_id}/wireframe`, das
        # `require_innendienst` vom Router bekommt und nicht aus der Signatur.
        innen = getattr(eintrag, "original_router", None)
        if innen is not None:
            yield from alle_routen(innen, tiefe + 1)
        else:
            yield from alle_routen(eintrag, tiefe + 1)


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "postgresql://localhost/kompagnon_test")
    from main import app

    schwach = defaultdict(list)
    stark = offen_ohne_anmeldung = 0

    for route in alle_routen(app):
        dependant = getattr(route, "dependant", None)
        if dependant is None or not getattr(route, "path", "").startswith("/api/"):
            continue

        gefunden = namen(dependant)
        if gefunden & STARK:
            stark += 1
        elif gefunden & SCHWACH:
            bereich = route.path.split("/")[2] if len(route.path.split("/")) > 2 else "?"
            schwach[bereich].append(route.path)
        else:
            offen_ohne_anmeldung += 1

    gesamt = stark + sum(len(v) for v in schwach.values()) + offen_ohne_anmeldung
    print(f"{gesamt} Routen unter /api/")
    print(f"  mit Rollen- oder Rechtepruefung:      {stark}")
    nur_angemeldet = sum(len(v) for v in schwach.values())
    print(f"  nur angemeldet, ohne Rollenpruefung: {nur_angemeldet}")
    print(f"  ohne jede Anmeldepruefung:            {offen_ohne_anmeldung}")

    if schwach:
        print("\nSchwach geschuetzt, nach Bereich:")
        for bereich, pfade in sorted(schwach.items(), key=lambda p: -len(p[1])):
            print(f"  {len(pfade):3}  /api/{bereich}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
