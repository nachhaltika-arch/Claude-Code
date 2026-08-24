"""Kein Dokument weist mehr auf einen Branch hin, den es nicht gibt (S5.1).

**Der Befund (BUCH-F0).** 13 Buch-Anleitungen begannen mit einem Pflicht-Check,
der `claude/kompagnon-automation-system-FapM9` als erwarteten Branch nannte.
Den Branch gibt es seit dem 01.05.2026 nicht mehr. Jede Session, die eine
dieser Dateien **ehrlich** abarbeitet, muss am eigenen Pflicht-Check stoppen
und „falscher Branch" melden. Wer ihn stattdessen ueberspringt, hat die
Schutzfunktion abgeschafft, fuer die er da ist.

**Es waren nicht 13.** Gezaehlt am 24.08.2026: 27 Dateien, 68 Fundstellen —
die zehn Prompts unter `docs/produkte/orders/` waren in BUCH-F0 nicht
aufgefuehrt. BUCH-F0 verlangt ausdruecklich, vor dem Ersetzen zu zaehlen; das
ist der Grund.

**Warum nicht alles ersetzt wurde.** Drei Dokumente *belegen* den Defekt,
statt ihn zu haben, und elf weitere Zeilen erklaeren im Fliesstext, dass es
den Branch nicht gibt. Dort zu ersetzen haette Saetze erzeugt, die behaupten,
`staging` existiere nicht.
"""
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[3]
TOT = "claude/kompagnon-automation-system-FapM9"

# Die Befunddokumente. Sie zitieren den toten Namen als Gegenstand.
BELEGE = {"BUCH-F0-Prompts-Branch-Korrektur.md", "BUCH-BEFUND-2026-08-24.md",
          "befundpaket-2026-08-22.md"}

# Zeilen, die den Namen beschreiben statt anzuweisen.
BESCHREIBT = re.compile(
    r"existiert nicht|gibt es .*nicht mehr|tote Angabe|verworfen|Widerspruch", re.I)


def _anweisungen() -> list:
    treffer = []
    for pfad in WURZEL.rglob("*.md"):
        if ".git" in pfad.parts or pfad.name in BELEGE:
            continue
        try:
            zeilen = pfad.read_text(encoding="utf-8").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        treffer += [
            f"{pfad.relative_to(WURZEL)}:{nr}"
            for nr, z in enumerate(zeilen, 1)
            if TOT in z and not BESCHREIBT.search(z)
        ]
    return treffer


def test_kein_pflicht_check_erwartet_einen_toten_branch():
    # Arrange / Act
    treffer = _anweisungen()

    # Assert
    assert not treffer, (
        "Diese Zeilen weisen auf einen Branch hin, den es nicht gibt — eine "
        "Anleitung, die an ihrem eigenen Pflicht-Check scheitert:\n  "
        + "\n  ".join(treffer)
    )


def test_die_belege_nennen_ihn_weiterhin():
    """Gegenprobe: Der Wächter darf die Befunddokumente nicht leerräumen.

    Ohne diesen Test wuerde ein spaeterer Sammelersatz die drei Dokumente
    mitnehmen — und mit ihnen den Beleg, dass der Defekt bestand.
    """
    # Arrange / Act
    gefunden = {
        p.name for p in WURZEL.rglob("*.md")
        if p.name in BELEGE and TOT in p.read_text(encoding="utf-8")
    }

    # Assert
    assert gefunden == BELEGE, f"Beleg verloren: {BELEGE - gefunden}"
