# -*- coding: utf-8 -*-
"""Text auf Bild oder Verlauf — aus den Punkten entschieden (L-17).

**Der Befund.** Die Kontrastmessung ging bis zum 01.09.2026 den Baum hinauf
und suchte den ersten deckenden Hintergrund. Fand sie stattdessen ein Bild
oder einen Verlauf, gab sie auf: **20 % des Textes** standen als
„unentscheidbar" in der Auswertung — gemeldet, aber nicht gewertet.

**Aus zwei Farben ist das wirklich nicht entscheidbar. Aus den gerenderten
Punkten schon.** Die Seite wird ein zweites Mal abgelichtet, diesmal mit
unsichtbarem Text; unter dem Kasten steht dann, was der Leser hinter den
Buchstaben hat.

**Gemessen wird der ungünstigste Punkt, nicht der durchschnittliche.** Ein
Verlauf ist an einem Ende hell und am anderen dunkel; ein Mittelwert bestünde,
während die Hälfte der Buchstaben unlesbar ist. Wer die schlechteste Stelle
besteht, besteht überall — die Aussage ist damit konservativ und nie zu
freundlich.

**Warum dieser Test ohne Browser auskommt.** Die Rechnung ist der Teil, der
falsch sein kann; ihn an einem selbst erzeugten Bild zu prüfen, dessen Antwort
vorher feststeht, ist genauer als ein Lauf gegen eine Seite, deren Farben sich
morgen ändern.
"""
import importlib.util
import pathlib

import pytest

WURZEL = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "bedienbarkeit_messen", WURZEL / "tools" / "bedienbarkeit_messen.py")
messen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(messen)

PIL = pytest.importorskip("PIL.Image")

SCHWARZ = (0, 0, 0)
WEISS = (255, 255, 255)


def _bild(punkte, breite=40, hoehe=10):
    """Ein Bild aus einer Funktion (x, y) → Farbe."""
    from PIL import Image
    b = Image.new("RGB", (breite, hoehe))
    b.putdata([punkte(x, y) for y in range(hoehe) for x in range(breite)])
    return b


def _kasten(farbe, schwelle=4.5, x=0, y=0, w=40, h=10):
    return {"x": x, "y": y, "w": w, "h": h, "farbe": list(farbe),
            "schwelle": schwelle, "laenge": 10, "beispiel": "Text"}


# ── Die Rechnung ─────────────────────────────────────────────────────

def test_schwarz_auf_weiss_ist_das_maximum():
    assert round(messen._kontrast(SCHWARZ, WEISS), 2) == 21.0


def test_gleiche_farbe_ist_das_minimum():
    assert round(messen._kontrast(WEISS, WEISS), 2) == 1.0


# ── Der ungünstigste Punkt ───────────────────────────────────────────

def test_auf_einer_flaeche_gilt_die_flaeche():
    bild = _bild(lambda x, y: WEISS)
    wert = messen._schlechtester_punkt(bild, _kasten(SCHWARZ), 40, 10)
    assert round(wert, 2) == 21.0


def test_ein_verlauf_wird_an_seiner_schlechtesten_stelle_gemessen():
    """**Der Kern.** Links weiß, rechts schwarz — schwarze Schrift darauf ist
    links tadellos und rechts unlesbar. Ein Mittelwert bestünde."""
    bild = _bild(lambda x, y: WEISS if x < 20 else SCHWARZ)

    wert = messen._schlechtester_punkt(bild, _kasten(SCHWARZ), 40, 10)

    assert round(wert, 2) == 1.0, "die dunkle Hälfte muss den Ausschlag geben"


def test_ein_einziger_schlechter_punkt_genuegt():
    """Ein Logo, ein heller Fleck im Bild — er trifft ein paar Buchstaben, und
    die sind dann weg. Eine Messung, die ihn wegmittelt, meldet grün."""
    def punkte(x, y):
        return (250, 250, 250) if (x, y) == (17, 4) else (20, 20, 20)

    bild = _bild(punkte)
    wert = messen._schlechtester_punkt(bild, _kasten(WEISS), 40, 10)

    assert wert < 1.2, f"der helle Fleck wurde weggemittelt (Wert {wert})"


def test_ein_kasten_ausserhalb_des_sichtfelds_zaehlt_nicht():
    """Nicht als bestanden und nicht als gefallen: Was nicht abgelichtet ist,
    wurde nicht gemessen — und eine Vermutung wäre schlimmer als eine Lücke."""
    bild = _bild(lambda x, y: WEISS)
    assert messen._schlechtester_punkt(
        bild, _kasten(SCHWARZ, y=200, h=10), 40, 10) is None
    assert messen._schlechtester_punkt(
        bild, _kasten(SCHWARZ, x=-40, w=20), 40, 10) is None


def test_ein_kasten_wird_am_sichtfeld_beschnitten_und_nicht_verworfen():
    """Halb sichtbar ist messbar — der sichtbare Teil zählt."""
    bild = _bild(lambda x, y: WEISS)
    wert = messen._schlechtester_punkt(
        bild, _kasten(SCHWARZ, x=30, w=40), 40, 10)
    assert wert is not None and round(wert, 2) == 21.0


def test_ein_foto_mit_vielen_farben_wird_nicht_uebersprungen():
    """`getcolors` gibt bei zu vielen Farben `None` zurück — der Rückfall geht
    dann Punkt für Punkt. Ohne ihn wäre ein Foto stillschweigend ungemessen,
    und genau Fotos sind der Fall, für den das hier gebaut ist."""
    def punkte(x, y):
        return ((x * 7) % 256, (y * 13) % 256, (x * y) % 256)

    bild = _bild(punkte, breite=300, hoehe=300)
    wert = messen._schlechtester_punkt(
        bild, _kasten(WEISS, w=300, h=300), 300, 300)

    assert wert is not None and wert > 1.0


# ── Im Browser: stimmen Kasten und Bildabzug überein? ────────────────
#
# **Das ist der Teil, den die Rechnung oben nicht abdeckt.** Sie kann perfekt
# sein und die Messung trotzdem falsch, wenn `getBoundingClientRect` und der
# Bildschirmabzug nicht denselben Ursprung haben — dann misst der Kasten die
# Farben eines anderen Elements, und niemand sieht es der Zahl an.

import os  # noqa: E402

PFLICHT = os.getenv("BROWSERTESTS_PFLICHT") == "1"

#: Links weiß, rechts schwarz — hart getrennt, damit die erwartete Antwort
#: ohne Rundung feststeht. Schwarze Schrift darauf ist rechts unlesbar.
PROBESEITE = """
<body style="margin:0">
  <div style="width:400px;height:60px;font-size:20px;color:#000;
       background:linear-gradient(to right,#fff 0%,#fff 50%,#000 50%,#000 100%)">
    Text auf einem Verlauf
  </div>
  <div style="width:400px;height:60px;font-size:20px;color:#fff;
       background:linear-gradient(to right,#111,#222)">
    Heller Text auf dunklem Grund
  </div>
</body>
"""


def _kein_browser(grund: str):
    if PFLICHT:
        pytest.fail(f"BROWSERTESTS_PFLICHT=1, aber {grund}")
    pytest.skip(grund)


@pytest.fixture(scope="module")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as f:                          # pragma: no cover
        _kein_browser(f"playwright fehlt: {f}")
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as f:                        # pragma: no cover
            _kein_browser(f"kein Chromium verfuegbar: {f}")
        yield b
        b.close()


def test_der_verlauf_wird_im_browser_richtig_entschieden(browser):
    """Beide Fälle in einem Lauf: der eine muss fallen, der andere bestehen.

    **Nur den Fehlerfall zu prüfen wäre die halbe Zusicherung** — eine
    Messung, die alles für gefallen erklärt, bestünde ihn ebenfalls.
    """
    seite = browser.new_context(viewport={"width": 800, "height": 400}).new_page()
    seite.set_content(PROBESEITE)

    erhoben = seite.evaluate(messen.ERHEBUNG_KONTRAST)
    kaesten = erhoben.pop("aufBild", [])
    assert len(kaesten) == 2, 'beide Stellen muessen als „auf Bild“ erkannt sein'

    ergebnis = messen._bild_kontraste(seite, kaesten)

    assert ergebnis["gefallen"] > 0, "Schwarz auf der dunklen Hälfte muss fallen"
    assert ergebnis["bestanden"] > 0, "Weiß auf dunklem Grund muss bestehen"
    fall = next(iter(ergebnis["faelle"]))
    assert "rgb(0,0,0)" in fall and "1.0 <" in fall


def test_der_stil_wird_nach_der_messung_wieder_entfernt(browser):
    """Sonst misst die Fokuserhebung gleich danach eine Seite ohne Text —
    und meldete triumphierend, dass nichts zu klein ist."""
    seite = browser.new_context(viewport={"width": 800, "height": 400}).new_page()
    seite.set_content(PROBESEITE)

    erhoben = seite.evaluate(messen.ERHEBUNG_KONTRAST)
    messen._bild_kontraste(seite, erhoben.pop("aufBild", []))

    farbe = seite.evaluate(
        "() => getComputedStyle(document.querySelector('div')).color")
    assert farbe != "rgba(0, 0, 0, 0)", "der Text ist unsichtbar geblieben"
