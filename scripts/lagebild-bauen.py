#!/usr/bin/env python3
"""Baut das KOMPAGNON-Lagebild aus der Lückenliste.

    python3 scripts/lagebild-bauen.py

**Warum als Skript und nicht von Hand.** Das Lagebild ist Davids
Entscheidungsgrundlage; ein Stand von gestern sieht aus wie einer von heute.
Es muss also nach jeder geschlossenen Lücke neu entstehen — und dann muss es
billig sein, sonst unterbleibt es.

**Die Zahlen zählt dieses Skript, nicht ein Mensch.** Am 22.08.2026 stand im
Kopf „7 von 11 Modulen grün"; gezählt waren es sechs. Jede Kennzahl hier
stammt aus den Daten, die darunter stehen. Auch die Zählweise selbst gehört
festgehalten: Bei den Dateigrößen (L-25) war die alte Methode nicht notiert,
und deshalb ließ sich nicht sagen, ob eine Zahl gestiegen war oder nur anders
gemessen wurde.

**Wahrheitsquelle ist `docs/soll-ist-analyse.md` § 3.** Das Lagebild ist ihre
Ansicht, nicht ihr Zwilling: Wer eine Lücke schließt, schreibt sie dort fort
und lässt danach dieses Skript laufen.

Ergebnis: `docs/lagebild/kompagnon-lagebild.html` — diese Datei wird als
Artifact veröffentlicht (derselbe Pfad hält dieselbe URL).
"""
import collections
import json
import pathlib
import re
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "docs" / "soll-ist-analyse.md"
VORLAGE = WURZEL / "docs" / "lagebild" / "vorlage.html"
PLANDATEN = WURZEL / "docs" / "lagebild" / "plan.json"
ZIEL = WURZEL / "docs" / "lagebild" / "kompagnon-lagebild.html"

#: Lücken, deren Zustand sich nicht aus der Tabellenform ablesen lässt.
#: Jede braucht einen Grund — sonst wird die Liste zum Ablagefach.
HANDGESETZT = {
    # (b) ist gebaut, aber nie gegen einen echten Dienst gelaufen. Weder
    # „offen" noch „geschlossen" trifft das.
    "L-58": "teilweise",
}


def _status(text: str, aufwand: str) -> str:
    """offen · teilweise · geschlossen — aus Durchstreichung und Aufwand.

    Ein durchgestrichener Titel heißt erledigt; steht daneben trotzdem ein
    Aufwand, ist ein Rest offen geblieben.
    """
    durchgestrichen = text.lstrip().startswith("~~")
    hat_aufwand = aufwand not in ("—", "-", "")
    if durchgestrichen and hat_aufwand:
        return "teilweise"
    if durchgestrichen or not hat_aufwand:
        return "geschlossen"
    return "offen"


def _herkunft(id_: str, text: str, beleg: str) -> str:
    """Woher der Befund stammt — die Frage, die David gestellt hat."""
    zusammen = (text + " " + beleg).lower()
    if "hubspot" in zusammen:
        return "HubSpot-Audit 19.08.2026"
    if "memberspot" in zusammen:
        return "Memberspot-Audit 19.08.2026"
    if "herstellerdoku" in beleg.lower():
        return "Herstellerdoku"
    if "stand-" in beleg:
        return "Tagesbericht " + beleg.replace("`", "")
    if "entscheidung" in beleg.lower():
        return "Entscheidung David"
    if "wc -l" in beleg:
        return "Zählung im Repo"
    if any(w in beleg.lower() for w in ("test", ".py", ".js", ".yml")):
        return "Am Code gemessen"
    return "Soll-Ist-Analyse"


def _titel(text: str) -> str:
    ohne = re.sub(r"~~", "", text)
    fett = re.match(r"\s*\*\*(.+?)\*\*", ohne)
    roh = fett.group(1) if fett else ohne
    roh = re.sub(r"[`*]", "", roh).strip()
    return (roh[:110] + "…") if len(roh) > 110 else roh


def _fliesstext(text: str, grenze: int = 460) -> str:
    s = re.sub(r"<br>", " ", text)
    s = re.sub(r"~~", "", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:grenze].rsplit(" ", 1)[0] + " …") if len(s) > grenze else s


def luecken_lesen() -> list:
    """Abschnitt 3 der Soll-Ist-Analyse als Liste von Einträgen."""
    text = QUELLE.read_text(encoding="utf-8")
    prio, heraus = None, []

    for zeile in text.splitlines():
        kopf = re.match(r"^### (P[0-3]) — (.+)$", zeile)
        if kopf:
            prio = (kopf.group(1), kopf.group(2))
            continue

        reihe = re.match(r"^\| (L-\d+) \| (.*) \| ([^|]*) \| ([^|]*) \|\s*$", zeile)
        if not (reihe and prio):
            continue

        id_, inhalt, aufwand, beleg = reihe.groups()
        aufwand, beleg = aufwand.strip(), beleg.strip()

        # Bei einigen Einträgen steht der Beleg in der Aufwandsspalte
        # („34 Tests"). Das sind erledigte; die Spalten wurden dort anders
        # befüllt, und ohne diese Korrektur zählt das Skript sie als offen.
        if re.match(r"^\d+ Tests$", aufwand):
            beleg, aufwand = aufwand, "—"

        heraus.append({
            "id": id_,
            "prio": prio[0],
            "bereich": prio[1],
            "aufwand": aufwand if aufwand not in ("—", "-", "") else "",
            "beleg": re.sub(r"`", "", beleg),
            "status": HANDGESETZT.get(id_, _status(inhalt, aufwand)),
            "titel": _titel(inhalt),
            "text": _fliesstext(inhalt),
            "herkunft": _herkunft(id_, inhalt, beleg),
            "datum": next(iter(re.findall(r"20\d\d-\d\d-\d\d", inhalt)), ""),
        })

    heraus.sort(key=lambda e: (e["prio"], e["id"]))
    return heraus


def module_gruen() -> int:
    """Wie viele Modulkarten in der Vorlage grün stehen — gezählt, nicht geglaubt."""
    return VORLAGE.read_text(encoding="utf-8").count('ampel:"a-gruen"')


def zahlen_block(luecken: list) -> str:
    z = collections.Counter(e["status"] for e in luecken)
    p0 = sum(1 for e in luecken if e["prio"] == "P0" and e["status"] != "geschlossen")
    gruen = module_gruen()

    felder = [
        (p0, "P0 · sofort", True),
        (z["offen"], "offen", False),
        (z["teilweise"], "teilweise", False),
        (z["geschlossen"], "geschlossen", False),
        (f'{gruen}<span style="font-size:19px">/11</span>', "Module grün", False),
        (3, "Pakete live", False),
    ]
    zeilen = "\n".join(
        f'      <div class="zahl{" dringend" if warn else ""}">'
        f'<div class="n">{wert}</div><div class="b">{name}</div></div>'
        for wert, name, warn in felder
    )
    return f'<div class="zahlen">\n{zeilen}\n    </div>'


def stand() -> str:
    kurz = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          cwd=WURZEL, capture_output=True, text=True).stdout.strip()
    datum = subprocess.run(["git", "log", "-1", "--format=%cd", "--date=format:%d.%m.%Y"],
                           cwd=WURZEL, capture_output=True, text=True).stdout.strip()
    return f"STAND {datum} · staging @ {kurz or 'unbekannt'}"


def main() -> int:
    if not QUELLE.exists() or not VORLAGE.exists():
        print(f"Fehlt: {QUELLE if not QUELLE.exists() else VORLAGE}", file=sys.stderr)
        return 2

    luecken = luecken_lesen()
    if not luecken:
        print("Keine Lücken gelesen — hat sich die Tabellenform geändert?", file=sys.stderr)
        return 2

    seite = VORLAGE.read_text(encoding="utf-8")
    plan = json.loads(PLANDATEN.read_text(encoding="utf-8")) if PLANDATEN.exists() else {
        "phasen": [], "blockiert": [], "spaeter": []}

    ersetzungen = {
        "/*__LUECKEN__*/[]": json.dumps(luecken, ensure_ascii=False),
        "/*__PLAN__*/{}": json.dumps(plan, ensure_ascii=False),
        "<!--__ZAHLEN__-->": zahlen_block(luecken),
        "<!--__STAND__-->": stand(),
    }
    for platzhalter, wert in ersetzungen.items():
        if platzhalter not in seite:
            print(f"Platzhalter fehlt in der Vorlage: {platzhalter}", file=sys.stderr)
            return 2
        seite = seite.replace(platzhalter, wert, 1)

    ZIEL.write_text(seite, encoding="utf-8")

    z = collections.Counter(e["status"] for e in luecken)
    p0 = sum(1 for e in luecken if e["prio"] == "P0" and e["status"] != "geschlossen")
    print(f"{ZIEL.relative_to(WURZEL)} — {len(luecken)} Lücken: "
          f"{z['offen']} offen, {z['teilweise']} teilweise, {z['geschlossen']} geschlossen "
          f"· P0 offen: {p0} · Module grün: {module_gruen()}/11")
    print("Jetzt als Artifact veröffentlichen (derselbe Pfad hält dieselbe URL).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
