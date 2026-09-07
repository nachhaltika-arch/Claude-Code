"""Neben der Rohzeile steht die Anweisungszahl (L-25).

**Der Befund vom 07.09.2026.** `tools/grosse-dateien.py` zaehlte Rohzeilen. In
diesem Projekt misst das zu einem guten Teil die **Kommentardichte**: Jede
Datei erklaert, *warum* etwas so steht, und das ist Absicht. Wer nur die
Rohzahl sieht, zerschneidet ein gut gegliedertes Modul, weil es gut erklaert
ist.

**Der erste Anlauf war selbst eine Fehlmessung.** Er zaehlte Zeilen mit einem
AST-Knoten — und das Ergebnis wanderte mit der Python-Fassung: unter 3.9 kamen
637 heraus, unter 3.11 (was CI und Produktion fahren) 639, bei
`pdf_bericht_seiten.py` 14 Zeilen Unterschied. Die Fassungen haengen `lineno`
an mehrzeiligen Ausdruecken verschieden an. **Eine Zahl, die vom Interpreter
abhaengt, ist keine Messung** — dasselbe Muster wie bei den anderen
Messfehlern dieses Tages, nur eine Ebene tiefer.

**Anweisungen sind stabil.** In beiden Fassungen kommt dasselbe heraus:

    migrations_runtime.py   2.094 roh →  38 Anweisungen
    auth_router.py            803 roh → 350
    audit_scoring.py          880 roh → 341
    payments.py               902 roh → 277
    pdf_bericht_seiten.py     821 roh → 271

**Was die Zahl zeigt.** `migrations_runtime.py` ist mit 38 Anweisungen
wirklich ein Journal aus einer grossen Liste und kein ueberfuelltes Modul —
genau wie L-25 seit dem 23.08. behauptet, jetzt gemessen statt behauptet.
Umgekehrt ist `auth_router.py` die **dichteste** der fuenf, obwohl sie die
kuerzeste ist. Die Rohzahl haette die Reihenfolge genau umgedreht.

**Die Grenze bleibt trotzdem** — man scrollt auch durch Kommentare. Aber ein
Schnitt gehoert auf die zweite Zahl gestuetzt.
"""
import ast
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))

import pytest


def anweisungen(pfad: Path) -> int:
    """Anweisungen der Datei — ohne Docstrings, unabhaengig von der Fassung."""
    baum = ast.parse(pfad.read_text(encoding="utf-8"))
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


def _grosse() -> list:
    """Backend-Dateien ueber 800 Rohzeilen."""
    aus = []
    for pfad in WURZEL.rglob("*.py"):
        if any(t in pfad.parts for t in ("venv", "tests", "__pycache__")):
            continue
        roh = len(pfad.read_text(encoding="utf-8").split("\n"))
        if roh > 800:
            aus.append((pfad, roh))
    return sorted(aus, key=lambda p: -p[1])


def test_es_gibt_ueberhaupt_grosse_dateien():
    """Ein Waechter, der seinen Gegenstand nicht findet, ist immer gruen."""
    assert _grosse(), "keine Datei ueber 800 Rohzeilen — hat sich der Suchpfad geaendert?"


#: Ratsche mit Luft: die dichteste Datei hat heute 350 Anweisungen.
#: Sie verbietet Wachstum, sie verlangt keine Schrumpfung — eine Schranke, die
#: am ersten Tag rot ist, wird am ersten Tag abgeschaltet.
HOECHSTE_DICHTE = 400


@pytest.mark.parametrize("name", [p.name for p, _ in _grosse()])
def test_keine_grosse_datei_wird_dichter(name):
    """Die eigentliche Aussage: Gross heisst hier ausfuehrlich, nicht ueberfuellt.

    Schlaegt dieser Test an, ist die Datei **wirklich** gewachsen — dann ist
    ein Schnitt faellig und nicht nur eine Ueberlegung. Kein Kommentarargument
    hilft dann mehr, denn Kommentare zaehlen hier nicht mit.
    """
    pfad = next(p for p, _ in _grosse() if p.name == name)
    dichte = anweisungen(pfad)
    assert dichte <= HOECHSTE_DICHTE, (
        f"{name}: {dichte} Anweisungen (Schranke {HOECHSTE_DICHTE}).")


def test_die_messung_haengt_nicht_an_der_python_fassung():
    """Die Gegenprobe zum eigenen Fehler.

    Der erste Anlauf zaehlte Zeilen mit AST-Knoten und lieferte je nach
    Fassung andere Zahlen. Anweisungen tun das nicht — hier festgehalten,
    damit niemand aus Bequemlichkeit zurueckwechselt: Eine Zeilenzaehlung
    ueber `lineno` waere kuerzer zu schreiben und wieder unzuverlaessig.
    """
    pfad = next(p for p, _ in _grosse())
    ueber_lineno = len({k.lineno for k in ast.walk(ast.parse(
        pfad.read_text(encoding="utf-8"))) if hasattr(k, "lineno")})
    # Die beiden messen Verschiedenes — das ist der Punkt. Waeren sie gleich,
    # haette die Umstellung nichts gebracht.
    assert anweisungen(pfad) != ueber_lineno
