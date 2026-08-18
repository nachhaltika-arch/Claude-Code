"""Keine einzige `async def` darf den synchronen KI-Client direkt aufrufen.

Geschwister von `test_keine_einzige_route_haengt_frei`: nicht eine Stelle
pruefen, sondern die Regel fuer alle. Am 17.08. kostete genau dieses Muster
im Impressum-Sucher drei 503er auf Staging; die Suche danach fand zehn
weitere Stellen. Ohne Sperre kommt die elfte beim naechsten Endpunkt zurueck,
und sie faellt erst unter Last auf.

Zwei Regeln:

1. In einer `async def` steht kein `client.messages.create(...)`, ausser der
   Aufruf wandert dort erkennbar in einen Thread.
2. Eine synchrone Funktion, die selbst `messages.create` enthaelt, wird nicht
   direkt aus einer `async def` gerufen — der Umweg ueber eine Ebene
   blockiert genauso.

Erlaubt ist der Weg ueber `services.ki_aufruf.frag_modell`.
"""
import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
UMHUELLUNGEN = ("to_thread", "run_in_executor", "run_sync")


def _dateien():
    for pfad in sorted(BACKEND.rglob("*.py")):
        teile = set(pfad.parts)
        if "venv" in teile or "tests" in teile or "__pycache__" in teile:
            continue
        yield pfad


def _ist_ki_aufruf(knoten):
    f = knoten.func
    return (
        isinstance(f, ast.Attribute)
        and f.attr == "create"
        and isinstance(f.value, ast.Attribute)
        and f.value.attr == "messages"
    )


def _aufrufname(knoten):
    f = knoten.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


class _Durchgang(ast.NodeVisitor):
    """Sammelt je Datei: KI-Aufrufe und Aufrufe fremder Funktionen,
    jeweils mit der umschliessenden Funktion und ob ein Thread uebernimmt."""

    def __init__(self):
        self.stapel = []           # (name, ist_async)
        self.tiefe = 0             # >0: wir stecken in to_thread & Co.
        self.ki_aufrufe = []       # (zeile, funktion, ist_async, umhuellt)
        self.aufrufe = []          # (zeile, ziel, funktion, ist_async, umhuellt)

    def _funktion(self, knoten, ist_async):
        self.stapel.append((knoten.name, ist_async))
        self.generic_visit(knoten)
        self.stapel.pop()

    def visit_FunctionDef(self, knoten):
        self._funktion(knoten, False)

    def visit_AsyncFunctionDef(self, knoten):
        self._funktion(knoten, True)

    def visit_Call(self, knoten):
        name = _aufrufname(knoten)
        if name in UMHUELLUNGEN:
            self.tiefe += 1
        if self.stapel:
            fn, ist_async = self.stapel[-1]
            if _ist_ki_aufruf(knoten):
                self.ki_aufrufe.append((knoten.lineno, fn, ist_async, self.tiefe > 0))
            elif name:
                self.aufrufe.append(
                    (knoten.lineno, name, fn, ist_async, self.tiefe > 0)
                )
        self.generic_visit(knoten)
        if name in UMHUELLUNGEN:
            self.tiefe -= 1


def _erhebung():
    je_datei = {}
    for pfad in _dateien():
        try:
            baum = ast.parse(pfad.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover — soll die Pruefung nicht stoppen
            continue
        durchgang = _Durchgang()
        durchgang.visit(baum)
        je_datei[pfad] = durchgang
    return je_datei


ERHEBUNG = _erhebung()


def test_die_erhebung_findet_ueberhaupt_ki_aufrufe():
    """Sonst pruefen die beiden Regeln unbemerkt eine leere Menge."""
    anzahl = sum(len(d.ki_aufrufe) for d in ERHEBUNG.values())

    assert anzahl >= 10, f"Nur {anzahl} KI-Aufrufe gefunden — Erhebung kaputt?"


def test_keine_async_funktion_ruft_das_modell_direkt():
    befunde = [
        f"{pfad.relative_to(BACKEND)}:{zeile} in async def {fn}"
        for pfad, durchgang in ERHEBUNG.items()
        for zeile, fn, ist_async, umhuellt in durchgang.ki_aufrufe
        if ist_async and not umhuellt
    ]

    assert not befunde, (
        "Diese Stellen halten die Ereignisschleife an, solange das Modell "
        "antwortet — der Server beantwortet in der Zeit auch Renders "
        "Gesundheitspruefung nicht (503). Ueber services.ki_aufruf.frag_modell "
        "fuehren:\n  " + "\n  ".join(befunde)
    )


def _blockierende_namen():
    """Synchrone Funktionen, die das Modell rufen — direkt oder ueber weitere
    synchrone Zwischenstufen. Zwei Ebenen sind kein Schutz: `generate_all`
    ruft `generate_llms_txt`, und das Modell antwortet trotzdem auf der
    Schleife des Aufrufers.

    Aufloesung nach Funktionsnamen, nicht nach Import — das kann eine
    gleichnamige Funktion mitnehmen. Ein Fehlalarm ist hier das kleinere
    Uebel: Er kostet einen Blick, ein uebersehener Fall einen 503.
    """
    blockierer = {
        fn
        for durchgang in ERHEBUNG.values()
        for _, fn, ist_async, umhuellt in durchgang.ki_aufrufe
        if not ist_async and not umhuellt
    }

    # Ausbreiten, bis nichts Neues mehr dazukommt.
    gewachsen = True
    while gewachsen:
        gewachsen = False
        for durchgang in ERHEBUNG.values():
            for _, ziel, fn, ist_async, umhuellt in durchgang.aufrufe:
                if ist_async or umhuellt or ziel not in blockierer:
                    continue
                if fn not in blockierer:
                    blockierer.add(fn)
                    gewachsen = True

    return blockierer


def test_keine_async_funktion_ruft_einen_blockierenden_helfer():
    blockierer = _blockierende_namen()

    befunde = [
        f"{pfad.relative_to(BACKEND)}:{zeile} — async def {fn} ruft {ziel}()"
        for pfad, durchgang in ERHEBUNG.items()
        for zeile, ziel, fn, ist_async, umhuellt in durchgang.aufrufe
        if ist_async and not umhuellt and ziel in blockierer
    ]

    assert not befunde, (
        "Eine Ebene dazwischen aendert nichts — der Aufruf laeuft trotzdem auf "
        "der Ereignisschleife:\n  " + "\n  ".join(befunde)
    )
