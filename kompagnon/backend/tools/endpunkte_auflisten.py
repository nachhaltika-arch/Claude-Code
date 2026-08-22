#!/usr/bin/env python3
"""Alle registrierten Endpunkte — als Maßstab vor und nach einem Umzug.

    cd kompagnon/backend
    ./venv/bin/python tools/endpunkte_auflisten.py > /tmp/endpunkte_vorher.txt
    …umbauen…
    ./venv/bin/python tools/endpunkte_auflisten.py > /tmp/endpunkte_nachher.txt
    diff /tmp/endpunkte_vorher.txt /tmp/endpunkte_nachher.txt

Ein leerer `diff` heißt: Kein Endpunkt ist verschwunden, keiner hat seinen
Pfad geändert. Das ist die Bedingung für einen gelungenen Umzug — einer, den
das Frontend bemerkt, ist ein misslungener.

**Warum `openapi()` und nicht `app.routes`.** Am 22.08.2026 gemessen:

    app.routes                71 Einträge
    app.openapi()["paths"]   383 Einträge

`app.routes` liefert unter Starlette 1.4 nur die oberste Ebene; die
eingebundenen Unter-Router fehlen darin. Ein Maßstab, der 71 von 383
Endpunkten kennt, meldet nach jeder Etappe „keine Abweichung" — auch wenn die
Hälfte fehlt. Genau dieser Irrtum hat mich an dem Tag einmal erwischt: Ein
Test suchte eine frisch gebaute Route über `app.routes` und meldete sie als
fehlend, während derselbe Aufruf sauber mit 200 antwortete.

**Die Zählweise gehört zum Ergebnis.** Bei den Dateigrößen (L-25) stand eine
Zahl ohne ihre Methode, und deshalb ließ sich später nicht sagen, ob sie
gestiegen war oder nur anders gemessen. Deshalb steht die Methode hier im
Kopf und die Gesamtzahl in der letzten Zeile der Ausgabe.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def endpunkte() -> list:
    """`METHODE  /pfad` je Endpunkt, alphabetisch — damit zwei Läufe
    vergleichbar sind."""
    from main import app

    heraus = []
    for pfad, eintrag in app.openapi()["paths"].items():
        for methode in eintrag:
            if methode.lower() in ("get", "post", "put", "patch", "delete"):
                heraus.append(f"{methode.upper():6} {pfad}")
    return sorted(heraus)


def main() -> int:
    liste = endpunkte()
    for zeile in liste:
        print(zeile)

    # Die Kennzahlen ans Ende, damit `diff` sie mitprüft: Verschiebt sich die
    # Gesamtzahl, steht es in derselben Ausgabe wie die Ursache.
    projekt = sum(1 for z in liste if "/api/projects" in z)
    print(f"\n# {len(liste)} Endpunkte gesamt, davon {projekt} unter /api/projects")
    print("# gezählt über app.openapi()['paths'] — nicht app.routes (siehe Kopf)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
