#!/usr/bin/env python3
"""Welche Dateien liegen über der 800-Zeilen-Grenze? (L-25)

    python3 tools/grosse-dateien.py            # beide Bereiche
    python3 tools/grosse-dateien.py --kurz     # nur die zwei Zahlen

**Warum es dieses Werkzeug gibt.** Am 24.08.2026 widersprach der Eintrag L-25
sich selbst: Die Überschrift sagte „9 im Backend", der Fließtext zwei Sätze
später „Backend damit von 10 auf **3** Dateien über der Grenze", und weiter
unten standen noch „26 Dateien" und „27 Dateien" aus früheren Ständen.
Nachgemessen waren es 3 und 14 — der Fließtext hatte recht, die Überschrift
war beim Fortschreiben nicht mitgezogen worden.

Das ist dieselbe Sorte Fehler wie L-84 und L-102: nicht die Daten waren
falsch, sondern eine Zahl, die jemand von Hand nachtragen musste. Deshalb
gibt es sie jetzt als Messung.

**Die Zählweise ist die, die L-25 selbst festgehalten hat** — sie steht dort
ausdrücklich da, damit „wer das nächste Mal zählt, dasselbe zählt":

    Frontend: find src \\( -name '*.js' -o -name '*.jsx' \\) ! -name '*.test.js'
    Backend:  alle *.py ohne venv/, tests/, __pycache__/

**Datendateien zählen mit, werden aber gekennzeichnet.** `templates_zusatz.js`
(3.121) und `wz2025.json` (10.142) sind Listen, keine Module; sie werden nicht
geteilt. Sie stillschweigend herauszurechnen wäre bequem und würde die Zahl
beschönigen — sie stehen deshalb drin, mit Hinweis.
"""
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent

#: Ab wann eine Datei als zu groß gilt (Regelwerk „Coding Style").
GRENZE = 800

#: Ordner, die nirgends mitzählen.
UEBERSPRINGEN = ("node_modules", "venv", "__pycache__", ".git", "build", "dist")

#: Dateien, die Daten führen statt Logik — sie werden bewusst nicht geteilt.
DATENDATEIEN = ("templates_zusatz.js", "wz2025.json")

BEREICHE = (
    {
        "titel": "Backend",
        "wurzel": WURZEL / "kompagnon" / "backend",
        "passt": lambda p: (
            p.suffix == ".py" and "tests" not in p.parts
        ),
    },
    {
        "titel": "Frontend",
        "wurzel": WURZEL / "kompagnon" / "frontend" / "src",
        "passt": lambda p: (
            p.suffix in (".js", ".jsx") and not p.name.endswith(".test.js")
        ),
    },
)


def _grosse(bereich: dict) -> list:
    """(Zeilen, Pfad) aller Dateien über der Grenze, größte zuerst."""
    wurzel = bereich["wurzel"]
    treffer = []
    for pfad in wurzel.rglob("*"):
        if not pfad.is_file():
            continue
        if any(teil in UEBERSPRINGEN for teil in pfad.parts):
            continue
        if not bereich["passt"](pfad):
            continue
        # **`count("\\n")`, nicht `splitlines()`.** Die in L-25 festgehaltene
        # Methode ist `wc -l`, und das zaehlt Zeilen*umbrueche*. Eine Datei
        # ohne abschliessenden Umbruch — `templates_zusatz.js` ist eine —
        # ergibt mit `splitlines()` eine Zeile mehr. Ein Werkzeug, das eine
        # andere Zahl nennt als die dokumentierte Methode, erzeugt genau die
        # Verwirrung, die es beenden soll.
        zeilen = pfad.read_text(encoding="utf-8", errors="ignore").count("\n")
        if zeilen > GRENZE:
            treffer.append((zeilen, pfad))
    return sorted(treffer, reverse=True)


def main(argv: list) -> int:
    kurz = "--kurz" in argv
    zahlen = []

    for bereich in BEREICHE:
        if not bereich["wurzel"].is_dir():
            print(f"Nicht gefunden: {bereich['wurzel']}", file=sys.stderr)
            return 2
        treffer = _grosse(bereich)
        zahlen.append((bereich["titel"], len(treffer)))
        if kurz:
            continue

        print(f"\n{bereich['titel']} — {len(treffer)} Dateien über "
              f"{GRENZE} Zeilen")
        for zeilen, pfad in treffer:
            hinweis = "  (Daten, wird nicht geteilt)" \
                if pfad.name in DATENDATEIEN else ""
            print(f"  {zeilen:>6}  {pfad.relative_to(WURZEL)}{hinweis}")

    zusammen = ", ".join(f"{n} im {t}" for t, n in zahlen)
    print(f"\nÜber der {GRENZE}-Zeilen-Grenze: {zusammen}.")
    if not kurz:
        print("Nicht jede große Datei gehört geteilt — ein chronologisches "
              "Journal\nund eine Datenliste sind groß aus gutem Grund. "
              "Diese Zahl nennt den Bestand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
