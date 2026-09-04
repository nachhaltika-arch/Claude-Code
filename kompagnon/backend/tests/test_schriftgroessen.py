# -*- coding: utf-8 -*-
"""Keine Schrift unter 12 px im Quelltext des Werkzeugs (L-17, Lesbarkeit).

**Warum es diesen Waechter gibt.** Die Groessen wurden in drei Schritten
gehoben — 11 px am 30.08., 10 px am 31.08., 9 und 8 px am 01.09.2026. Jeder
Schritt war Handarbeit ueber Dutzende Dateien, und jeder war in dem Moment
rueckgaengig gemacht, in dem die naechste Komponente wieder `fontSize: 9`
schreibt. Eine einmal geleerte Liste bleibt nur leer, wenn etwas sie leer
haelt.

**Was dieser Waechter kann und was nicht.** Er zaehlt **Stilangaben im
Quelltext**, nicht gerenderten Text. Lighthouse prueft „Document uses legible
font sizes" am **Gerenderten** und gewichtet nach Zeichenmenge; eine Angabe,
die einmal vorkommt, zaehlt hier so viel wie eine in jeder Tabellenzeile. Die
Zahl, auf die es dem Nutzer ankommt, misst `tools/schriftgroessen_messen.py`
am laufenden Werkzeug. Dieser Test ist die billige Vorstufe: Er faengt die
neue Fundstelle beim Hinzufuegen, nicht die Auswirkung beim Anzeigen.

**Drei Schreibformen, weil drei vorkamen.** Am 01.09. fand die reine Suche
nach `fontSize: <Zahl>` 112 Stellen — und uebersah zwei weitere Formen:
`fontSize: '0.65rem'` (10,4 px) auf einem Abzeichen und `text-[11px]` in zwei
Bausteinen der Bibliothek. Die letzten beiden gehen in **Kundenseiten**; dort
misst unser eigener Pruefkatalog die Lesbarkeit, wir haetten also
ausgeliefert, was wir selbst abwerten. Wer nur nach der erwarteten Form sucht,
findet die erwartete Zahl — dasselbe Muster wie in `messfehler_eigene_zahlen`.

**Und der Waechter wird selbst geprueft.** Die Suchroutine laeuft gegen einen
Beispieltext, der jede der drei Formen einmal zu klein und einmal gross genug
enthaelt. Ohne diese Gegenprobe waere „null Fundstellen" auch dann wahr, wenn
der Ausdruck nichts mehr trifft — ein Waechter, der beim Nichtmessen gruen
bleibt, ist schlimmer als keiner (siehe `waechter_ohne_wirkung`).
"""
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent          # kompagnon/
QUELLE = WURZEL / "frontend" / "src"

#: Unterhalb dieser Groesse gilt Text als zu klein. Der Wert stammt nicht von
#: uns: Lighthouse besteht die Lesbarkeitspruefung, wenn der ueberwiegende
#: Teil der Zeichen mindestens 12 px misst.
MINDESTGROESSE_PX = 12

#: Ein Wurzelschriftgrad von 16 px — der Browservorgabewert, den weder
#: `index.css` noch `tokens.css` aendert. Nur damit laesst sich `rem` in `px`
#: umrechnen; steht dort einmal etwas anderes, ist diese Umrechnung falsch.
WURZELGROESSE_PX = 16

_ENDUNGEN = (".jsx", ".js", ".css", ".html")

# Zahl ohne Einheit: `fontSize: 9`. Die Grenzpruefung `(?![\d.])` ist nicht
# Zierrat — ohne sie machte die Hebung am 31.08. aus `11.5` ein `12.5`.
_ZAHL = re.compile(r"fontSize:\s*(\d+(?:\.\d+)?)(?![\d.])")
# Zeichenkette mit Einheit: `fontSize: '0.65rem'`, `font-size: 11px`.
_MIT_EINHEIT = re.compile(
    r"(?:fontSize|font-size)\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)(px|rem|em)\b"
)
# Tailwind-Sondermass: `text-[11px]`. Die benannten Stufen (`text-xs` = 12 px)
# sind bewusst nicht erfasst — sie stehen fest und liegen alle auf oder ueber
# der Grenze.
_TAILWIND = re.compile(r"text-\[(\d+(?:\.\d+)?)px\]")


def _in_px(wert: float, einheit: str) -> float:
    if einheit == "px":
        return wert
    return wert * WURZELGROESSE_PX      # rem und em, beide an der Wurzel


def zu_kleine_stellen(text: str) -> list[tuple[int, str, float]]:
    """(Zeilennummer, Fundstueck, Groesse in px) fuer alles unter der Grenze."""
    funde: list[tuple[int, str, float]] = []
    for nr, zeile in enumerate(text.splitlines(), start=1):
        for treffer in _ZAHL.finditer(zeile):
            px = float(treffer.group(1))
            if px < MINDESTGROESSE_PX:
                funde.append((nr, treffer.group(0), px))
        for treffer in _MIT_EINHEIT.finditer(zeile):
            px = _in_px(float(treffer.group(1)), treffer.group(2))
            if px < MINDESTGROESSE_PX:
                funde.append((nr, treffer.group(0), px))
        for treffer in _TAILWIND.finditer(zeile):
            px = float(treffer.group(1))
            if px < MINDESTGROESSE_PX:
                funde.append((nr, treffer.group(0), px))
    return funde


def _quelldateien() -> list[Path]:
    return sorted(p for p in QUELLE.rglob("*") if p.suffix in _ENDUNGEN and p.is_file())


def test_die_suche_findet_alle_drei_schreibformen():
    """Gegenprobe: der Ausdruck trifft, was er treffen soll — und sonst nichts."""
    # Arrange — je Form eine zu kleine und eine ausreichende Angabe.
    beispiel = "\n".join([
        "<div style={{ fontSize: 9 }} />",              # zu klein
        "<div style={{ fontSize: 12 }} />",             # genau die Grenze
        "<div style={{ fontSize: 11.5 }} />",           # zu klein, Bruchzahl
        "style={{ fontSize: '0.65rem' }}",              # 10,4 px
        "style={{ fontSize: '0.75rem' }}",              # 12 px
        '<p class="text-[11px]">klein</p>',             # zu klein
        '<p class="text-xs">passt</p>',                 # benannte Stufe
        "const projektnummer = 9;",                     # keine Schriftgroesse
    ])

    # Act
    funde = zu_kleine_stellen(beispiel)

    # Assert
    assert [f[2] for f in funde] == [9.0, 11.5, 10.4, 11.0]


def test_kein_text_unter_zwoelf_pixeln_im_frontend():
    """Der eigentliche Waechter: null Fundstellen im ausgelieferten Quelltext."""
    # Arrange
    dateien = _quelldateien()

    # Act
    funde = [
        f"{p.relative_to(QUELLE)}:{nr} {stueck} ({px:g} px)"
        for p in dateien
        for nr, stueck, px in zu_kleine_stellen(p.read_text(encoding="utf-8"))
    ]

    # Assert
    assert not funde, (
        f"{len(funde)} Schriftgroessen unter {MINDESTGROESSE_PX} px:\n"
        + "\n".join(funde)
    )


def test_der_waechter_liest_ueberhaupt_dateien():
    """Ohne das waere „null Fundstellen" auch bei leerem Suchbereich wahr.

    Genau dieser Fehler ist am 29.08. passiert: Die Messung lief gegen die
    404-Seite und meldete „0 % zu kleiner Text".
    """
    dateien = _quelldateien()
    assert len(dateien) > 200, f"nur {len(dateien)} Quelldateien gefunden"
    assert any("fontSize" in p.read_text(encoding="utf-8") for p in dateien)
