#!/usr/bin/env python3
"""Welche Route ruft niemand auf? (L-101)

    cd kompagnon/backend
    ./venv/bin/python tools/unaufgerufene-routen.py
    ./venv/bin/python tools/unaufgerufene-routen.py --alle   # auch die erklärten

**Warum es dieses Werkzeug gibt.** „Gebaut, nicht angeschlossen" ist in
diesem System eine eigene Fehlerfamilie, und sie wurde bisher jedes Mal von
Hand gefunden:

* **L-55** — ein Wächter, den niemand aufrief
* **L-79** — die seitenweise Freigabe ist erreichbar, nur ruft sie keiner
* **L-11** — ``_fernet_available()`` wurde nie gerufen und beim Aufräumen
  als überflüssig gelöscht; sie war nicht überflüssig, sondern nicht
  angeschlossen
* **24.08.2026** — ``POST /api/projects/{id}/time``: Die Margenrechnung hängt
  an diesen Stunden, und im ganzen Frontend ruft sie niemand ein

Viermal derselbe Fund. Eine Route, die niemand aufruft, ist kein Fehler —
aber sie ist eine **Frage**, und die soll nicht vom Zufall abhängen.

**Das Gegenstück** ist ``tests/test_frontend_adressen.py``: Es prüft, dass
jeder Aufruf des Frontends eine Route trifft. Beide lesen dieselbe Grundlage
(``tools/adressen.py``), damit sie nicht auseinanderdriften.

**Warum kein Test.** „Ruft niemand auf" ist oft genau richtig: Webhooks
kommen von außen, das Widget lebt auf fremden Seiten, Portalrouten hängen an
einem Einmal-Token, der Scheduler ruft intern. Ein Test wäre dauerhaft rot
oder bekäme eine Ausnahmeliste, die niemand pflegt. Dieses Werkzeug sortiert
stattdessen: Was von außen gerufen wird, steht unter „erklärt"; alles andere
ist eine offene Frage.
"""
import pathlib
import sys

# Wie die Nachbarwerkzeuge: Das Backend liegt eine Ebene hoeher, und von dort
# kommen `main` und `tools.adressen`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools.adressen import (  # noqa: E402
    gerufene_adressen,
    normalisieren,
    routen_mit_methode,
)

#: Adressen, die planmäßig nicht aus dem Frontend gerufen werden.
#: Jede Gruppe braucht einen Grund — sonst wird die Liste zum Ablagefach.
ERKLAERT = (
    ("/api/webhooks/", "Webhook — wird von aussen gerufen (Stripe, Brevo, Netlify)"),
    ("/api/widget/", "Widget — lebt eingebettet auf fremden Seiten"),
    ("/api/portal/", "Kundenportal — haengt am Einmal-Token aus der Mail"),
    ("/api/public/", "Oeffentlich — Landingpage und Freigabelinks"),
    ("/api/health", "Betriebspruefung"),
    ("/health", "Betriebspruefung"),
    ("/docs", "FastAPIs eigene Oberflaeche"),
    ("/redoc", "FastAPIs eigene Oberflaeche"),
    ("/openapi.json", "FastAPIs eigenes Schema"),
)


def _erklaerung(pfad: str):
    for anfang, grund in ERKLAERT:
        if pfad.startswith(anfang):
            return grund
    return None


def main(argv: list) -> int:
    alle = "--alle" in argv

    gerufen = gerufene_adressen()
    routen = routen_mit_methode()

    offen, erklaert = [], []
    for methode, pfad in routen:
        if normalisieren(pfad) in gerufen:
            continue
        grund = _erklaerung(pfad)
        (erklaert if grund else offen).append((methode, pfad, grund))

    offen.sort(key=lambda e: (e[1], e[0]))
    erklaert.sort(key=lambda e: (e[1], e[0]))

    print(f"Backend: {len(routen)} Endpunkte · Frontend ruft "
          f"{len(gerufen)} verschiedene Adressen")

    print(f"\nOhne Aufrufer im Frontend und ohne Erklaerung — {len(offen)}:")
    if not offen:
        print("  keine")
    for methode, pfad, _ in offen:
        print(f"  {methode:<7} {pfad}")

    print(f"\nErklaert — {len(erklaert)} (mit --alle einzeln):")
    if alle:
        for methode, pfad, grund in erklaert:
            print(f"  {methode:<7} {pfad}\n            {grund}")
    else:
        gruende = {}
        for _, _, grund in erklaert:
            gruende[grund] = gruende.get(grund, 0) + 1
        for grund, anzahl in sorted(gruende.items(), key=lambda g: -g[1]):
            print(f"  {anzahl:>4}  {grund}")

    print("\nEine Route ohne Aufrufer ist kein Fehler — sie ist eine Frage: "
          "\nfehlt der Knopf, oder ist die Route ueberfluessig geworden?")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
