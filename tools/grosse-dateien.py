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
import ast
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


def anweisungen(pfad) -> int:
    """Wie viele **Anweisungen** eine Datei enthaelt — ohne Docstrings.

    **Warum diese zweite Zahl seit dem 07.09.2026 danebensteht (L-25).** Die
    Rohzahl misst in diesem Projekt zu einem guten Teil die Kommentardichte:
    Jede Datei erklaert, *warum* etwas so steht, und das ist Absicht. Wer nur
    Rohzeilen sieht, zerschneidet ein gut gegliedertes Modul, weil es gut
    erklaert ist.

    **Warum Anweisungen und nicht „Code-Zeilen".** Der erste Anlauf zaehlte
    Zeilen mit einem AST-Knoten. Das Ergebnis wanderte mit der Python-Fassung:
    unter 3.9 kamen 637, unter 3.11 (was CI und Produktion fahren) 639 heraus,
    bei `pdf_bericht_seiten.py` sogar 14 Zeilen Unterschied — die Fassungen
    haengen `lineno` an mehrzeiligen Ausdruecken verschieden an. Eine Zahl, die
    vom Interpreter abhaengt, ist keine Messung. Anweisungen sind stabil: In
    beiden Fassungen kommt dasselbe heraus, nachgeprueft.

    **Was die Zahl zeigt.** `migrations_runtime.py` hat 2.094 Zeilen und **38
    Anweisungen** — es ist wirklich ein Journal aus einer grossen Liste und
    kein ueberfuelltes Modul, genau wie L-25 es seit dem 23.08. behauptet.
    Umgekehrt ist `auth_router.py` mit 350 Anweisungen die dichteste der fuenf,
    obwohl sie die kuerzeste ist.

    Fuer alles ausser Python gibt es diese Zahl nicht; dort steht ein Strich.
    """
    if pfad.suffix != ".py":
        return -1
    try:
        baum = ast.parse(pfad.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return -1
    anzahl = 0
    for knoten in ast.walk(baum):
        if not isinstance(knoten, ast.stmt):
            continue
        if (isinstance(knoten, ast.Expr)
                and isinstance(getattr(knoten, "value", None), ast.Constant)
                and isinstance(knoten.value.value, str)):
            continue                      # Docstring
        anzahl += 1
    return anzahl


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
            anz = anweisungen(pfad)
            davon = f"{anz:>5} Anweisungen" if anz >= 0 else "    — Anweisungen"
            print(f"  {zeilen:>6} roh  {davon}  {pfad.relative_to(WURZEL)}{hinweis}")

    zusammen = ", ".join(f"{n} im {t}" for t, n in zahlen)
    print(f"\nÜber der {GRENZE}-Zeilen-Grenze: {zusammen}.")
    if not kurz:
        print("Nicht jede große Datei gehört geteilt — ein chronologisches "
              "Journal\nund eine Datenliste sind groß aus gutem Grund. "
              "Diese Zahl nennt den Bestand.")
        print("\nDie zweite Spalte zählt Anweisungen — was die Datei **tut**, "
              "ohne\nKommentare und Docstrings. Sie ist unabhängig von der "
              "Python-Fassung,\ndie Rohzahl misst hier zu gutem Teil die "
              "Ausführlichkeit, die dieses\nProjekt bewusst pflegt. Ein "
              "Schnitt gehört auf die zweite Zahl gestützt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
