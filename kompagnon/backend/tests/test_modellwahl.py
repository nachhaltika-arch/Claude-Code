"""Welches Modell aufgerufen wird — und ob das Denken dazu passt.

**Warum es diesen Test gibt.** Beim Modellwechsel am 21.08.2026 kamen drei
Dinge zusammen, die einzeln harmlos aussehen und zusammen jeden KI-Aufruf im
Haus kaputtmachen:

1. `claude-sonnet-4-20250514` stand an **16** Stellen — ein Datums-Schnappschuss
   mit Rueckzugsdatum 15.06.2026. Ein zurueckgezogenes Modell antwortet mit 404,
   und keine dieser Stellen haette das gemeldet.
2. Auf Sonnet 5 und Opus 5 ist **adaptives Denken die Vorgabe**, wenn `thinking`
   fehlt. Auf den Vorgaengern war es das Gegenteil.
3. **21 Stellen lesen `content[0]`.** Mit eingeschaltetem Denken steht dort ein
   Denkblock, nicht der Text — und `max_tokens` (an manchen Stellen 200) teilen
   sich Denken und Antwort.

Aus 2 und 3 folgt: Wer das Modell hebt, ohne `thinking` zu setzen, bekommt
leere Antworten und abgeschnittenes JSON — ohne Fehlermeldung. Deshalb pruefen
die Tests hier beides, und nicht nur die Modell-ID.
"""
import pathlib
import re

WURZEL = pathlib.Path(__file__).resolve().parent.parent

#: Modelle, die im Produktivcode stehen duerfen. Wer eines ergaenzt, denkt
#: bewusst darueber nach — genau das ist der Zweck der Liste.
ERLAUBT = {"claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"}

#: Der eine Aufruf, der bewusst denkt: sichere Extraktion (`b.type == "text"`),
#: grosszuegiges Budget, und die Bewertung eines Audits lohnt das Nachdenken.
MIT_DENKEN = {"services/audit_ai.py", "routers/component_library.py"}

_MODELL = re.compile(r"claude-(?:opus|sonnet|haiku|fable|mythos)-[a-z0-9-]*")
_AUFRUF = re.compile(r"messages\.(?:create|stream)\(")


def _produktivdateien():
    for pfad in sorted(WURZEL.rglob("*.py")):
        teile = pfad.relative_to(WURZEL).parts
        if teile[0] in ("tests", "venv") or "__pycache__" in teile:
            continue
        yield pfad


def test_kein_zurueckgezogenes_modell():
    """Ein Datums-Schnappschuss ist ein Ablaufdatum ohne Wecker."""
    fund = {}
    for pfad in _produktivdateien():
        for name in set(_MODELL.findall(pfad.read_text())):
            if name not in ERLAUBT:
                fund.setdefault(str(pfad.relative_to(WURZEL)), []).append(name)

    assert fund == {}, f"Unbekannte Modelle: {fund}"


def test_jeder_aufruf_entscheidet_ueber_das_denken():
    """Kein Aufruf darf `thinking` weglassen und damit die Vorgabe erben.

    Die Vorgabe hat sich mit Sonnet 5 umgedreht. Ein Aufruf ohne Angabe traf
    frueher „kein Denken" und trifft jetzt „adaptiv" — dieselbe Zeile, anderes
    Verhalten. Wer das Denken will, schreibt es hin; wer es nicht will, auch.
    """
    ohne = []
    for pfad in _produktivdateien():
        name = str(pfad.relative_to(WURZEL))
        if name in MIT_DENKEN:
            continue
        zeilen = pfad.read_text().split("\n")
        for i, z in enumerate(zeilen):
            if not _AUFRUF.search(z):
                continue
            # Ein Durchreiche-Helfer (`create(**argumente)`) nennt weder Modell
            # noch Denken — beides kommt vom Aufrufer, und der wird hier
            # ohnehin geprueft. `services/ki_aufruf.py` ist genau das.
            if "**" in "\n".join(zeilen[i:i + 3]):
                continue
            # Der Aufruf reicht bis zur schliessenden Klammer; 16 Zeilen decken
            # jeden Aufruf im Bestand ab (laengster: 11 Zeilen).
            if "thinking" not in "\n".join(zeilen[i:i + 16]):
                ohne.append(f"{name}:{i + 1}")

    assert ohne == [], f"Aufrufe ohne Denk-Entscheidung: {ohne}"


def test_die_ausnahmen_liest_den_textblock_und_nicht_den_ersten():
    """Wer denken laesst, darf nicht `content[0]` lesen.

    Das ist die Bedingung, unter der die Ausnahmen ueberhaupt zulaessig sind.
    """
    for name in MIT_DENKEN:
        quelle = (WURZEL / name).read_text()
        assert 'b.type == "text"' in quelle or "_extract_text_from_response" in quelle, (
            f"{name} denkt, liest aber nicht gezielt den Textblock"
        )
