#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Der Systemdurchlauf — ein Lauf ueber Optik, Funktion und Konsistenz.

    python3 scripts/systemdurchlauf.py
    python3 scripts/systemdurchlauf.py --alle        # auch die aussortierten
    python3 scripts/systemdurchlauf.py --laufzeit docs/durchlauf/laufzeit-<datum>.json

**Was er ist.** Ein Dirigent, kein neues Messwerkzeug. Das Repo hat gute
Einzelmessungen; was fehlte, war die feste Reihenfolge, ein gemeinsames
Befundformat und der Filter, der verhindert, dass jede Woche dieselbe Liste
erscheint.

**Der Ablauf.**

    0  Selbstprobe  — findet jede Stufe noch ihr eigenes Beispiel?
    1  Erheben      — jede Stufe misst ihre Fehlerklasse
    2  Belegen      — ohne Datei:Zeile oder Messwert faellt der Befund raus
    3  Nachpruefen  — Stichprobe am Gegenstand, bevor gemeldet wird
    4  Abgleichen   — steht der Gegenstand schon als L-Nummer? Rueckfall?
    5  Quittieren   — ist er frueher abgeraeumt worden?
    6  Berichten    — nach Ebenen sortiert, mit Beleg je Zeile
    7  Uebernehmen  — **von Hand**: David entscheidet, was L-Nummer wird

**Schritt 0 steht vor allem anderen.** Elf Stufen melden heute null Befunde.
Das kann Ruhe heissen oder Blindheit, und von aussen sind beide nicht zu
unterscheiden. Die Selbstprobe legt Beispieldateien mit genau den gesuchten
Fehlern an; findet eine Stufe ihr eigenes Beispiel nicht, steht das **vor**
jedem Sachbefund im Bericht. Beim Bau hat sie sofort etwas gefunden: Die
Stufe „Geheimnis in der Adresse" kannte nur englische Wortteile und waere in
einem Repo mit `schluessel` und `geheimnis` blind geblieben.

**Schritt 3 ist nicht optional.** Beim Bauen hat er sechs Fehlalarme
abgefangen, die sonst als Systemfehler in der Lueckenliste gestanden haetten.

Ergebnis: `docs/durchlauf/befund-<datum>.md` und `befunde-<datum>.json`.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.durchlauf import selbstprobe                    # noqa: E402
from tools.durchlauf.befund import Befund, WURZEL, sieben  # noqa: E402
from tools.durchlauf.register import REGISTER, ausfuehren  # noqa: E402
from tools.durchlauf.werkzeuge import python_der_anwendung  # noqa: E402

ZIELORDNER = WURZEL / "docs" / "durchlauf"
PRUEFLISTE = ZIELORDNER / "pruefliste.json"

EBENEN_TITEL = {
    "datenbank":     "Ebene 1 — Datenbank",
    "schnittstelle": "Ebene 2 — Schnittstelle",
    "frontend":      "Ebene 3 — Frontend",
    "browser":       "Ebene 4 — Browser",
    "optik":         "Optik",
    "konsistenz":    "Konsistenz und Bauwerk",
}

BEDARF_TEXT = {
    "quelltext": "liest nur den Quelltext",
    "anwendung": "braucht die Backend-Umgebung",
    "frontend":  "braucht node_modules",
    "dienst":    "braucht einen laufenden Dienst",
}


def pruefliste_faellig() -> tuple[list[dict], int]:
    """Die Urteilsfragen, die ueberfaellig sind — und wie viele es gibt."""
    if not PRUEFLISTE.exists():
        return [], 0
    try:
        daten = json.loads(PRUEFLISTE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], 0
    fragen = daten.get("fragen", [])
    heute = datetime.date.today()
    faellig = []
    for frage in fragen:
        zuletzt = (frage.get("zuletzt") or "").strip()
        if not zuletzt:
            frage["_tage"] = None
            faellig.append(frage)
            continue
        try:
            her = (heute - datetime.date.fromisoformat(zuletzt)).days
        except ValueError:
            continue
        if her >= int(frage.get("intervall_tage", 90)):
            frage["_tage"] = her
            faellig.append(frage)
    return faellig, len(fragen)


def bericht(neu, gefuehrt, quittiert, messungen, blind, nicht_gemessen,
            laufzeit, alle) -> str:
    heute = datetime.date.today().isoformat()
    z: list[str] = []
    z.append(f"# Systemdurchlauf — Befund vom {heute}")
    z.append("")
    z.append("> **Dieser Bericht ist ein Vorschlag, keine Lueckenliste.** Was hier steht,")
    z.append("> ist gemessen; was daraus eine L-Nummer wird, entscheidest du. Erst danach")
    z.append("> wandert es in `docs/soll-ist-analyse.md` und ins Lagebild.")
    z.append("")

    if blind:
        z.append("## ⚠ Zuerst: der Durchlauf misst nicht richtig")
        z.append("")
        z.append("Die Selbstprobe legt Beispieldateien an, die genau die gesuchten Fehler")
        z.append("enthalten. Die folgenden Stufen haben ihr eigenes Beispiel **nicht**")
        z.append("gefunden. Solange das so ist, bedeutet jede Null dieser Stufen nichts —")
        z.append("und der Rest des Berichts steht auf wackligem Grund.")
        z.append("")
        for b in blind:
            z.append(f"* **{b['titel']}** — `{b['beleg']}`")
        z.append("")

    z.append("## Was gelaufen ist")
    z.append("")
    z.append("| Stufe | Bedarf | Befunde | Grundgesamtheit |")
    z.append("|---|---|---:|---|")
    for name, bedarf, anzahl, notiz in messungen:
        z.append(f"| {name} | {BEDARF_TEXT.get(bedarf, bedarf)} | {anzahl} | {notiz or '—'} |")
    summe = sum(m[2] for m in messungen)
    z.append(f"| **Summe** | | **{summe}** | |")
    z.append("")
    z.append(f"Davon **{len(neu)} neu**, {len(gefuehrt)} bereits als L-Nummer gefuehrt, "
             f"{len(quittiert)} frueher abgeraeumt.")
    z.append("")

    if nicht_gemessen:
        z.append("### Nicht gemessen — und das ist nicht dasselbe wie in Ordnung")
        z.append("")
        for name, grund in nicht_gemessen:
            z.append(f"* **{name}** — {grund}")
        z.append("")

    rueckfaelle = [e for e in neu if e.get("rueckfall")]
    if rueckfaelle:
        z.append("## Zu pruefen: Gegenstand steht in einem erledigten Eintrag")
        z.append("")
        z.append("Der Abgleich ist ein **Textvergleich**, kein Urteil: Der Gegenstand")
        z.append("kommt in einer Zeile vor, die als erledigt gefuehrt wird. Das ist")
        z.append("entweder ein Rueckfall — dann der wichtigste Befund des Laufs — oder")
        z.append("der Eintrag erwaehnt die Sache nur nebenbei.")
        z.append("")
        z.append("| Ebene | Befund | Beleg | steht unter |")
        z.append("|---|---|---|---|")
        for e in rueckfaelle:
            z.append(f"| {e['ebene']} | {e['titel']} | `{e['beleg'][:110]}` | {e.get('luecke','')} |")
        z.append("")

    z.append("## Neue Befunde")
    z.append("")
    uebrig = [e for e in neu if not e.get("rueckfall")]
    if not uebrig:
        z.append("Keine. Der Lauf hat nichts gefunden, was nicht schon gefuehrt oder")
        z.append("abgeraeumt waere.")
        z.append("")
    rang = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for ebene, titel in EBENEN_TITEL.items():
        teil = [e for e in uebrig if e["ebene"] == ebene]
        if not teil:
            continue
        z.append(f"### {titel}")
        z.append("")
        for e in sorted(teil, key=lambda x: rang.get(x["vorschlag"], 9)):
            z.append(f"**{e['titel']}** · Vorschlag {e['vorschlag']}")
            z.append("")
            z.append(e["einzelheiten"])
            z.append("")
            z.append(f"*Beleg:* `{e['beleg']}`")
            z.append("")
            z.append(f"*Kennung:* `{e['kennung']}` — in `docs/durchlauf/quittiert.json` "
                     "eintragen, um den Befund dauerhaft abzuraeumen.")
            z.append("")

    if alle and gefuehrt:
        z.append("## Bereits als L-Nummer gefuehrt")
        z.append("")
        for e in gefuehrt:
            z.append(f"* {e.get('luecke','')} — {e['titel']}")
        z.append("")
    if alle and quittiert:
        z.append("## Frueher abgeraeumt")
        z.append("")
        for e in quittiert:
            z.append(f"* {e['titel']} — *{e.get('grund','ohne Grund')}*")
        z.append("")

    faellig, gesamt = pruefliste_faellig()
    z.append("## Was keine Maschine beantwortet")
    z.append("")
    if gesamt == 0:
        z.append("`docs/durchlauf/pruefliste.json` fehlt — die Urteilsfragen werden nicht gefuehrt.")
    else:
        z.append(f"{gesamt} Fragen gefuehrt, **{len(faellig)} davon faellig**. Wer eine")
        z.append("beantwortet, traegt das Datum bei `zuletzt` ein — dann verschwindet sie")
        z.append("bis zum naechsten Mal.")
        z.append("")
        for frage in faellig:
            wann = ("noch nie beantwortet" if frage.get("_tage") is None
                    else f"zuletzt vor {frage['_tage']} Tagen")
            z.append(f"**{frage['frage']}** · {wann}")
            z.append("")
            z.append(f"{frage.get('warum','')}")
            z.append("")
    z.append("")

    z.append("## Was dieser Lauf nicht gesehen hat")
    z.append("")
    if not laufzeit:
        z.append("* **Alles, was nur am laufenden Dienst sichtbar ist** — Statuscodes,")
        z.append("  Konsolenfehler, leere Seiten, tatsaechliche Kontraste. Dafuer")
        z.append("  `scripts/durchlauf-laufzeit.py` gegen Staging fahren und das")
        z.append("  Ergebnis mit `--laufzeit` uebergeben.")
    z.append("* **Ob eine Anzeige stimmt.** Der Lauf sieht, dass ein Feld gelesen wird,")
    z.append("  nicht, ob der richtige Wert darin steht.")
    z.append("* **Gestaltung.** Farben werden gegen die Vorgabe gemessen; ob eine")
    z.append("  Oberflaeche gut ist, steht in `docs/ux-soll-ist-kas.md`.")
    z.append("* **Verhaltensaenderungen fremder Bibliotheken.** Ein Import gelingt und")
    z.append("  liefert trotzdem etwas anderes als frueher — L-140 war so. Dagegen")
    z.append("  hilft nur ein Test, der das Verhalten festhaelt.")
    z.append("")
    return "\n".join(z)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--alle", action="store_true", help="auch aussortierte Befunde zeigen")
    p.add_argument("--still", action="store_true", help="nur die Dateipfade ausgeben")
    p.add_argument("--laufzeit", metavar="DATEI",
                   help="Ergebnis von scripts/durchlauf-laufzeit.py mit aufnehmen")
    p.add_argument("--nur", metavar="BEDARF",
                   choices=("quelltext", "anwendung", "frontend", "dienst"),
                   help="nur Stufen mit diesem Bedarf ausfuehren")
    args = p.parse_args()

    # Schritt 0 — misst der Durchlauf ueberhaupt noch?
    blind = [b.als_dict() for b in selbstprobe.laufen()]
    if blind and not args.still:
        for b in blind:
            print(f"  BLIND: {b['titel']}", file=sys.stderr)

    hat_anwendung = python_der_anwendung() is not None
    hat_frontend = (WURZEL / "kompagnon" / "frontend" / "node_modules").is_dir()
    befunde: list[Befund] = []
    messungen: list[tuple[str, str, int, str]] = []
    nicht_gemessen: list[tuple[str, str]] = []

    for stufe in REGISTER:
        if args.nur and stufe.bedarf != args.nur:
            continue
        if stufe.bedarf == "frontend" and not hat_frontend:
            nicht_gemessen.append((
                stufe.name,
                "`kompagnon/frontend/node_modules` fehlt. Diese Stufe laesst die "
                "vorhandenen Jest-Tests laufen — sie rechnen jedes benutzte Farbpaar "
                "in **beiden** Tokensaetzen gegen WCAG AA und sind gruendlicher als "
                "jede Nachbildung."))
            continue
        if stufe.bedarf == "anwendung" and not hat_anwendung:
            nicht_gemessen.append((
                stufe.name,
                "kein Interpreter mit den Backend-Abhaengigkeiten gefunden "
                "(`kompagnon/backend/venv`). Diese Stufe misst an der geladenen "
                "Anwendung und sieht Dinge, die aus dem Quelltext nicht ableitbar "
                "sind — sie gehoert nachgeholt, nicht uebergangen."))
            continue
        teil, notiz = ausfuehren(stufe)
        befunde.extend(teil)
        messungen.append((stufe.name, stufe.bedarf, len(teil), notiz))
        if not args.still:
            print(f"  {stufe.name:42s} {len(teil):3d}   {notiz[:56]}", file=sys.stderr)

    if args.laufzeit:
        aus_datei = json.loads(pathlib.Path(args.laufzeit).read_text(encoding="utf-8"))
        roh = aus_datei.get("befunde", [])
        befunde.extend(Befund(**b) for b in roh)
        messungen.append(("Laufzeit (Browser)", "dienst", len(roh),
                          f"{aus_datei.get('gemessen_anzahl', '?')} Seiten gegen "
                          f"{aus_datei.get('basis', '?')}"))
    else:
        nicht_gemessen.append((
            "Laufzeit (Browser)",
            "nicht gelaufen. `scripts/durchlauf-laufzeit.py` gegen Staging fahren "
            "und das Ergebnis mit `--laufzeit` uebergeben."))

    befunde.extend(Befund(**b) for b in blind)
    neu, gefuehrt, quittiert = sieben(befunde)

    ZIELORDNER.mkdir(parents=True, exist_ok=True)
    heute = datetime.date.today().isoformat()
    md = ZIELORDNER / f"befund-{heute}.md"
    js = ZIELORDNER / f"befunde-{heute}.json"
    md.write_text(bericht(neu, gefuehrt, quittiert, messungen, blind,
                          nicht_gemessen, bool(args.laufzeit), args.alle),
                  encoding="utf-8")
    js.write_text(json.dumps(
        {"datum": heute, "blind": blind, "neu": neu, "gefuehrt": gefuehrt,
         "quittiert": quittiert, "nicht_gemessen": nicht_gemessen},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(md.relative_to(WURZEL))
    print(js.relative_to(WURZEL))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
