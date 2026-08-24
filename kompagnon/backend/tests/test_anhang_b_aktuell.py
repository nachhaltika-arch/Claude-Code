"""Anhang B muss zum Katalog passen (BUCH-F3, S5.7 im Kern).

**Der Befund, der dahintersteht.** Am 24.08.2026 wich die Spezifikation in
sechs Punkten vom Katalog ab — SEO mit 18 statt 15 Punkten, Summe 103 statt
100, ein siebtes SEO-Kriterium, das nirgends stand. Die Regel „Änderungen am
Maßstab erfolgen hier zuerst" war in **null von sechs** Fällen befolgt worden.

Deshalb wird Anhang B erzeugt (`scripts/standard-export.py`) und nicht
gepflegt. Dieser Test hält fest, dass die abgelegte Fassung dem Katalog
entspricht: Wer ein Kriterium ändert und den Export vergisst, bekommt hier
einen roten Lauf statt ein falsch gedrucktes Buch.

**Er schreibt nichts.** Er erzeugt in ein temporäres Verzeichnis und
vergleicht — ein Test, der die Datei repariert, die er prüfen soll, hält
gar nichts fest.
"""
import pathlib
import subprocess
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parents[3]
SKRIPT = WURZEL / "scripts" / "standard-export.py"
ANHANG = (WURZEL / "docs" / "Buch"
          / "Buch - Kompagnon - Homepage Standard v2"
          / "ANHANG-B-Schwellentabellen.md")
KATALOG = WURZEL / "kompagnon" / "backend" / "services" / "audit_criteria.py"


def test_das_exportskript_liegt_im_repo():
    assert SKRIPT.exists(), (
        "scripts/standard-export.py fehlt — dann ist Anhang B wieder von Hand "
        "gepflegt, und genau das war der Befund."
    )


def test_der_abgelegte_anhang_entspricht_dem_katalog():
    # Arrange
    assert ANHANG.exists(), f"{ANHANG} fehlt"

    with tempfile.TemporaryDirectory() as ordner:
        frisch = pathlib.Path(ordner) / "anhang-b.md"

        # Act
        lauf = subprocess.run(
            [sys.executable, str(SKRIPT), str(KATALOG), str(frisch)],
            capture_output=True, text=True,
        )
        assert lauf.returncode == 0, lauf.stderr[-800:]

        # Assert
        erzeugt = frisch.read_text(encoding="utf-8")

    abgelegt = ANHANG.read_text(encoding="utf-8")
    if abgelegt != erzeugt:
        alt = abgelegt.splitlines()
        neu = erzeugt.splitlines()
        abweichung = next(
            (f"Zeile {i + 1}: abgelegt {a!r} — erzeugt {b!r}"
             for i, (a, b) in enumerate(zip(alt, neu)) if a != b),
            f"Länge: abgelegt {len(alt)}, erzeugt {len(neu)}")
        raise AssertionError(
            "Anhang B und der Katalog gehen auseinander. Neu erzeugen mit "
            f"`python3 scripts/standard-export.py`. Erste Abweichung — "
            f"{abweichung}"
        )
