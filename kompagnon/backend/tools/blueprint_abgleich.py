#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blueprint gegen den laufenden Dienst — was der Test nicht kann.

**Warum es das gibt (L-35).** Produktiv ist bewusst **nicht**
blueprint-verwaltet (Entscheidung David, 27.08.2026): Einen Blueprint auf
laufende Dienste anzuwenden uebernimmt sie entweder oder legt sie neu an, und
bei einem Dienst mit Datentraeger ist das ein Ausfallrisiko fuer einen
Nutzen, den ein Ein-Personen-Betrieb nie einloest.

Die Dateien **beschreiben** also, sie steuern nicht. Damit ist die einzige
sinnvolle Zusicherung: **Es faellt auf, wenn die Beschreibung nicht mehr
stimmt.** `tests/test_blueprint_abgleich.py` haelt die Dateien gegeneinander
— das laeuft ohne Zugangsdaten bei jedem CI-Lauf. Ob sie zur **Wirklichkeit**
passen, kann nur dieses Werkzeug sagen, und dafuer braucht es einen
Render-Schluessel.

**Warum kein CI-Job daraus wurde.** Ein Prueflauf, der bei jedem Push eine
fremde API befragt, wird rot, wenn diese API kurz nicht antwortet — und ein
Tor, das aus fremden Gruenden rot wird, wird abgeschaltet. Dieses Werkzeug
laeuft auf Zuruf, vor einem Umzug oder wenn etwas komisch aussieht.

    RENDER_API_KEY=rnd_… ./venv/bin/python tools/blueprint_abgleich.py

**Was es meldet und was nicht:** Verglichen werden **Namen**, nie Werte. Ein
Werkzeug, das Geheimnisse ausgibt, waere gefaehrlicher als die Luecke, die es
finden soll — dieselbe Regel wie bei `/health` (L-139).
"""
import os
import re
import sys
import json
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent      # kompagnon/

#: Welche Datei welchen Dienst beschreibt. Die Namen sind die, die die
#: Render-API fuehrt — nicht die aus dem Blueprint: Der nannte bis zum
#: 24.08. `kompagnon-backend`, und so heisst der **stillgelegte**
#: Oregon-Dienst (L-34).
PAARE = (
    ("render-staging.yaml",   "kompagnon-backend-staging"),
    ("render-produktiv.yaml", "kompagnon-backend-fra"),
)


def blueprint_schluessel(datei: Path) -> set:
    return set(re.findall(r"^\s*- key:\s*([A-Za-z_][A-Za-z0-9_]*)",
                          datei.read_text(encoding="utf-8"), re.M))


def _hole(pfad: str, schluessel: str):
    anfrage = urllib.request.Request(
        f"https://api.render.com/v1{pfad}",
        headers={"Authorization": f"Bearer {schluessel}",
                 "Accept": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        return json.loads(antwort.read())


def dienst_schluessel(dienst_id: str, schluessel: str) -> set:
    """Die Namen der Umgebungsvariablen eines Dienstes — **ohne Werte**."""
    seiten, cursor = set(), ""
    while True:
        pfad = f"/services/{dienst_id}/env-vars?limit=100"
        if cursor:
            pfad += f"&cursor={cursor}"
        antwort = _hole(pfad, schluessel)
        if not antwort:
            break
        for eintrag in antwort:
            seiten.add(eintrag["envVar"]["key"])
            cursor = eintrag.get("cursor", "")
        if len(antwort) < 100:
            break
    return seiten


def main() -> int:
    schluessel = os.getenv("RENDER_API_KEY", "").strip()
    if not schluessel:
        print("RENDER_API_KEY fehlt. Ohne ihn kann nur der Test laufen,\n"
              "der die Dateien gegeneinander haelt:\n"
              "  ./venv/bin/python -m pytest tests/test_blueprint_abgleich.py")
        return 2

    try:
        dienste = {d["service"]["name"]: d["service"]["id"]
                   for d in _hole("/services?limit=100", schluessel)}
    except urllib.error.HTTPError as fehler:
        print(f"Render antwortete {fehler.code}. Traegt der Schluessel?")
        return 2

    abweichungen = 0
    for dateiname, dienstname in PAARE:
        datei = WURZEL / dateiname
        print(f"\n── {dateiname}  ↔  {dienstname} " + "─" * 24)

        if dienstname not in dienste:
            print(f"   Dienst nicht gefunden. Vorhanden: "
                  f"{', '.join(sorted(dienste))}")
            abweichungen += 1
            continue

        aus_datei = blueprint_schluessel(datei)
        am_dienst = dienst_schluessel(dienste[dienstname], schluessel)

        nur_datei = sorted(aus_datei - am_dienst)
        nur_dienst = sorted(am_dienst - aus_datei)

        print(f"   Blueprint {len(aus_datei)} · Dienst {len(am_dienst)} · "
              f"gemeinsam {len(aus_datei & am_dienst)}")
        if nur_datei:
            print(f"   nur im Blueprint ({len(nur_datei)}) — beschrieben, "
                  f"aber nicht gesetzt:\n      {', '.join(nur_datei)}")
        if nur_dienst:
            print(f"   nur am Dienst ({len(nur_dienst)}) — gesetzt, aber "
                  f"nirgends beschrieben:\n      {', '.join(nur_dienst)}")
        if not nur_datei and not nur_dienst:
            print("   deckungsgleich")
        abweichungen += len(nur_datei) + len(nur_dienst)

    print(f"\n{abweichungen} Abweichung(en). Namen verglichen, keine Werte.")
    return 1 if abweichungen else 0


if __name__ == "__main__":
    sys.exit(main())
