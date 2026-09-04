#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Der Systemdurchlauf — ein Lauf ueber Optik, Funktion und Konsistenz.

    python3 scripts/systemdurchlauf.py              # statische Stufen
    python3 scripts/systemdurchlauf.py --alle       # auch die aussortierten zeigen

**Was er ist.** Ein Dirigent, kein neues Messwerkzeug. Das Repo hat bereits
gute Einzelmessungen (`tools/`, `kompagnon/backend/tools/`); was fehlte, war
die feste Reihenfolge, ein gemeinsames Befundformat und der Filter, der
verhindert, dass jede Woche dieselbe Liste erscheint.

**Der Ablauf in sechs Schritten.**

    1  Erheben      — jede Stufe misst ihre Fehlerklasse am Quelltext
    2  Belegen      — ein Befund ohne Datei-und-Zeile wird verworfen
    3  Abgleichen   — steht der Gegenstand schon als L-Nummer in der Liste?
    4  Quittieren   — hat David ihn schon einmal abgeraeumt?
    5  Berichten    — Markdown mit Beleg je Zeile, nach Ebene sortiert
    6  Uebernehmen  — **von Hand**: David hakt ab, dann neue L-Nummern

Schritt 6 ist bewusst nicht automatisch. Eine Liste, die sich selbst
verlaengert, waechst schneller, als jemand sie abarbeitet — und die echten
offenen Punkte gehen darin unter.

Ergebnis: `docs/durchlauf/befund-<datum>.md` und `.../befunde-<datum>.json`.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.durchlauf.befund import Befund, WURZEL, sieben   # noqa: E402
from tools.durchlauf.stufen import ALLE_STUFEN             # noqa: E402

ZIELORDNER = WURZEL / "docs" / "durchlauf"

EBENEN_TITEL = {
    "datenbank":    "Ebene 1 — Datenbank",
    "schnittstelle": "Ebene 2 — Schnittstelle",
    "frontend":     "Ebene 3 — Frontend",
    "browser":      "Ebene 4 — Browser",
    "optik":        "Optik",
    "konsistenz":   "Konsistenz",
}


def _tabelle(eintraege: list[dict], spalte_extra: str = "") -> list[str]:
    kopf = "| Ebene | Befund | Beleg | Vorschlag |"
    if spalte_extra:
        kopf = f"| Ebene | Befund | Beleg | {spalte_extra} |"
    zeilen = [kopf, "|---|---|---|---|"]
    for e in eintraege:
        letzte = e.get("luecke") or e.get("grund") or e["vorschlag"]
        zeilen.append(
            f"| {e['ebene']} | {e['titel']} | `{e['beleg'][:120]}` | {letzte} |"
        )
    return zeilen


def bericht(neu: list[dict], gefuehrt: list[dict], quittiert: list[dict],
            gemessen: dict[str, int], alle: bool) -> str:
    heute = datetime.date.today().isoformat()
    z: list[str] = []
    z.append(f"# Systemdurchlauf — Befund vom {heute}")
    z.append("")
    z.append("> **Dieser Bericht ist ein Vorschlag, keine Lueckenliste.** Was hier steht,")
    z.append("> ist gemessen; was daraus eine L-Nummer wird, entscheidest du. Erst danach")
    z.append("> wandert es in `docs/soll-ist-analyse.md` und ins Lagebild.")
    z.append("")
    z.append("## Was gelaufen ist")
    z.append("")
    z.append("| Stufe | Befunde erhoben |")
    z.append("|---|---:|")
    for name, anzahl in gemessen.items():
        z.append(f"| {name} | {anzahl} |")
    z.append(f"| **Summe** | **{sum(gemessen.values())}** |")
    z.append("")
    z.append(f"Davon **{len(neu)} neu**, {len(gefuehrt)} bereits als L-Nummer gefuehrt, "
             f"{len(quittiert)} frueher abgeraeumt.")
    z.append("")

    rueckfaelle = [e for e in neu if e.get("rueckfall")]
    if rueckfaelle:
        z.append("## Rueckfaelle — die Liste sagt erledigt, die Messung nicht")
        z.append("")
        z.extend(_tabelle(rueckfaelle, "steht unter"))
        z.append("")

    z.append("## Neue Befunde")
    z.append("")
    if not neu:
        z.append("Keine. Der Lauf hat nichts gefunden, was nicht schon gefuehrt oder abgeraeumt waere.")
        z.append("")
    for ebene, titel in EBENEN_TITEL.items():
        teil = [e for e in neu if e["ebene"] == ebene and not e.get("rueckfall")]
        if not teil:
            continue
        z.append(f"### {titel}")
        z.append("")
        for e in sorted(teil, key=lambda x: x["vorschlag"]):
            z.append(f"**{e['titel']}** · Vorschlag {e['vorschlag']}")
            z.append("")
            z.append(f"{e['einzelheiten']}")
            z.append("")
            z.append(f"*Beleg:* `{e['beleg']}`")
            z.append("")
            z.append(f"*Kennung:* `{e['kennung']}` — diese Zeichenkette in "
                     "`docs/durchlauf/quittiert.json` eintragen, um den Befund "
                     "dauerhaft abzuraeumen.")
            z.append("")

    if alle and gefuehrt:
        z.append("## Bereits als L-Nummer gefuehrt")
        z.append("")
        z.extend(_tabelle(gefuehrt, "steht unter"))
        z.append("")
    if alle and quittiert:
        z.append("## Frueher abgeraeumt")
        z.append("")
        z.extend(_tabelle(quittiert, "Grund"))
        z.append("")

    z.append("## Was dieser Lauf **nicht** gesehen hat")
    z.append("")
    z.append("* **Alles, was nur am laufenden Dienst sichtbar ist** — Statuscodes,")
    z.append("  Konsolenfehler, leere Seiten, tatsaechliche Kontraste. Das misst")
    z.append("  `scripts/durchlauf-laufzeit.py` gegen Staging und braucht Netz.")
    z.append("* **Ob eine Anzeige stimmt.** Der Lauf sieht, dass ein Feld gelesen wird,")
    z.append("  nicht, ob der richtige Wert darin steht.")
    z.append("* **Routen ohne Aufrufer** in der genauen Fassung — dafuer gibt es")
    z.append("  `kompagnon/backend/tools/unaufgerufene-routen.py`, das die geladene")
    z.append("  Anwendung liest und damit genauer ist als jede Textmessung.")
    z.append("")
    return "\n".join(z)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--alle", action="store_true", help="auch aussortierte Befunde zeigen")
    p.add_argument("--still", action="store_true", help="nur die Dateipfade ausgeben")
    p.add_argument("--laufzeit", metavar="DATEI",
                   help="Ergebnis von scripts/durchlauf-laufzeit.py mit aufnehmen")
    args = p.parse_args()

    befunde, gemessen = [], {}
    for name, stufe in ALLE_STUFEN:
        teil = stufe()
        gemessen[name] = len(teil)
        befunde.extend(teil)
        if not args.still:
            print(f"  {name:34s} {len(teil):3d}", file=sys.stderr)

    # Die Laufzeitstufe laeuft getrennt (sie braucht Netz und Browser); ihre
    # Befunde werden hier eingesammelt, damit **ein** Bericht entsteht.
    if args.laufzeit:
        aus_datei = json.loads(pathlib.Path(args.laufzeit).read_text(encoding="utf-8"))
        roh = aus_datei.get("befunde", [])
        gemessen["Laufzeit (Browser)"] = len(roh)
        befunde.extend(Befund(**b) for b in roh)
        if not args.still:
            print(f"  {'Laufzeit (Browser)':34s} {len(roh):3d}"
                  f"   [{aus_datei.get('basis', '?')}]", file=sys.stderr)
    else:
        gemessen["Laufzeit (Browser) — nicht gelaufen"] = 0

    neu, gefuehrt, quittiert = sieben(befunde)

    ZIELORDNER.mkdir(parents=True, exist_ok=True)
    heute = datetime.date.today().isoformat()
    md = ZIELORDNER / f"befund-{heute}.md"
    js = ZIELORDNER / f"befunde-{heute}.json"
    md.write_text(bericht(neu, gefuehrt, quittiert, gemessen, args.alle), encoding="utf-8")
    js.write_text(json.dumps(
        {"datum": heute, "neu": neu, "gefuehrt": gefuehrt, "quittiert": quittiert},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(md.relative_to(WURZEL))
    print(js.relative_to(WURZEL))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
