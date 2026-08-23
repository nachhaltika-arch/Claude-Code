#!/usr/bin/env python3
"""Welche npm-Befunde erreichen die ausgelieferte Anwendung? (L-08)

**Warum es dieses Werkzeug gibt.** `npm audit` meldete am 22.08.2026 vierzig-
vier Befunde, davon 19 hoch und 2 kritisch. Die Zahl klingt alarmierend und
stand so in der Lueckenliste. Nachgemessen kamen **vierzig davon allein ueber
`react-scripts`** herein — ein Bauwerkzeug, das nie an einen Besucher
ausgeliefert wird. Ein RCE in `shell-quote` ist ausnutzbar, wenn jemand den
Bauvorgang mit boesartiger Eingabe faehrt; im Browser des Kunden laeuft davon
nichts.

**Die Falle bei der Einordnung.** Man koennte meinen, `dependencies` sei
Laufzeit und `devDependencies` sei Bauzeit. Bei Create React App stimmt das
**nicht**: `react-scripts`, `postcss` und `tailwindcss` stehen allesamt unter
`dependencies` und sind trotzdem reines Bauwerkzeug. Der erste Anlauf dieser
Messung ist genau daran gescheitert und meldete „0 Bauzeit-Befunde".

Entschieden wird deshalb daran, **worueber** ein Befund hereinkommt, und die
Bauwerkzeuge stehen namentlich unten.

Aufruf im Frontend-Verzeichnis:

    python3 ../../tools/npm-befunde-einordnen.py
"""
import json
import subprocess
import sys

#: Direkte Eintraege, die trotz `dependencies` reines Bauwerkzeug sind.
#: Kein Anwendungscode importiert sie; sie erscheinen in keinem Bundle.
#: Nachgeprueft am 22.08.2026 — `postcss` und `tailwindcss` haengen an
#: `postcss.config.js`, `react-scripts` ist der Bauvorgang selbst.
BAUWERKZEUG = {"react-scripts", "postcss", "tailwindcss"}


def audit() -> dict:
    lauf = subprocess.run(["npm", "audit", "--json"],
                          capture_output=True, text=True)
    if not lauf.stdout.strip():
        sys.exit(f"npm audit lieferte nichts: {lauf.stderr[:200]}")
    return json.loads(lauf.stdout)


def direkte() -> set:
    with open("package.json", encoding="utf-8") as datei:
        paket = json.load(datei)
    return set(paket.get("dependencies", {})) | set(paket.get("devDependencies", {}))


def wurzeln(name: str, befunde: dict, direkt: set, gesehen=None) -> set:
    """Ueber welche **direkten** Eintraege dieser Befund hereinkommt."""
    gesehen = gesehen or set()
    if name in gesehen:
        return set()
    gesehen.add(name)

    eintrag = befunde.get(name)
    if not eintrag:
        return set()

    gefunden = {name} if name in direkt else set()
    for eltern in eintrag.get("effects", []):
        gefunden |= wurzeln(eltern, befunde, direkt, gesehen)
    return gefunden


def main() -> int:
    daten = audit()
    befunde = daten.get("vulnerabilities", {})
    direkt = direkte()

    nur_bau, ausgeliefert = [], []
    for name, eintrag in sorted(befunde.items()):
        ueber = wurzeln(name, befunde, direkt) - BAUWERKZEUG
        ziel = ausgeliefert if ueber else nur_bau
        ziel.append((eintrag.get("severity", "?"), name, sorted(ueber)))

    stand = daten.get("metadata", {}).get("vulnerabilities", {})
    print(f"npm audit: {stand.get('total', 0)} Befunde "
          f"({stand.get('critical', 0)} kritisch, {stand.get('high', 0)} hoch)")
    print(f"  nur ueber Bauwerkzeug: {len(nur_bau)}")
    print(f"  im Auslieferungscode:  {len(ausgeliefert)}")

    if not ausgeliefert:
        print("\nKein Befund erreicht den Code, der beim Besucher laeuft.")
        return 0

    print("\nDiese erreichen den Besucher:")
    for schwere, name, ueber in ausgeliefert:
        print(f"  {schwere:9} {name:26} ueber {', '.join(ueber)}")
    # Absichtlich kein Fehlschlag: Das Werkzeug ordnet ein, es urteilt nicht.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
