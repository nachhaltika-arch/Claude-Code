"""Die Spezifikation nennt fuer L1 und L2 dieselben Pflichtfelder wie der Code.

**Der Befund (K05-1, K05-2, verschaerft in Kapitel 12).** `audit-anforderungen-
2026-08-11.md` § 3.2 verlangte fuer L1 die **Kammer** und fuer L2 **Zwecke** und
**Auftragsverarbeiter**. Der Code zaehlt keines der drei zu `core`. Das war keine
Auslassung, sondern eine Abweichung des Codes von der freigegebenen
Spezifikation — und sie fiel niemandem auf, weil nichts sie pruefte.

Kapitel 16 nennt das Muster beim Namen: „Die Spezifikationsdokumente sind aelter
als der Code und werden nicht nachgezogen." Dieser Test zieht nach.

**Warum ueber den Text und nicht ueber einen Import.** Die Feldnamen im Code
(`register`, `vertretung`) sind Kuerzel; die Spezifikation schreibt fuer Menschen
(„Register/USt-ID", „Vertretungsberechtigter"). Gepruefte Zuordnung statt
Zeichenvergleich — mit der Folge, dass ein neues Feld im Code hier ein
`KeyError` ausloest und nicht stillschweigend durchrutscht.
"""
import re
from pathlib import Path

import pytest

from services.audit_collectors import _evaluate_datenschutz, _evaluate_impressum

SPEZIFIKATION = (Path(__file__).resolve().parents[3] / "docs" / "Audit"
                 / "audit-anforderungen-2026-08-11.md")

# Feldname im Code → die Worte, unter denen die Spezifikation ihn fuehrt.
WORTE = {
    "anschrift": "Anschrift",
    "kontakt": "Kontakt",
    "vertretung": "Vertretungsberechtigter",
    "register": "Register/USt-ID",
    "kammer": "Kammer",
    "verantwortlicher": "Verantwortlicher",
    "rechtsgrundlage": "Rechtsgrundlage",
    "betroffenenrechte": "Betroffenenrechte",
    "aufsichtsbehoerde": "Aufsichtsbehörde",
    "speicherdauer": "Speicherdauer",
}

SEITE = "<html><body>Impressum</body></html>"


def _zeile(code: str) -> str:
    text = SPEZIFIKATION.read_text(encoding="utf-8")
    treffer = re.search(rf"^\| {code} \| (.+?) \| \d+ \|", text, re.M)
    assert treffer, f"Zeile {code} nicht in § 3.2 gefunden"
    return treffer.group(1)


def _pflichtfelder(auswerter) -> tuple:
    """Die `core`-Felder — abgelesen an dem, was `complete` tatsaechlich kippt."""
    ergebnis = auswerter("https://example.test/x", SEITE)
    return tuple(ergebnis["missing"])


@pytest.mark.parametrize("code, auswerter", [
    ("L1", _evaluate_impressum),
    ("L2", _evaluate_datenschutz),
])
def test_die_spezifikation_nennt_genau_die_gemessenen_pflichtfelder(code, auswerter):
    # Arrange
    zeile = _zeile(code)
    gemessen = _pflichtfelder(auswerter)

    # Act
    fehlt_im_text = [f for f in gemessen if WORTE[f] not in zeile]
    zuviel_im_text = [
        f for f, wort in WORTE.items()
        if f not in gemessen and re.search(rf"\b{re.escape(wort)}\b", zeile)
    ]

    # Assert
    assert not fehlt_im_text, (
        f"{code}: Der Code verlangt {fehlt_im_text}, die Spezifikation nennt es nicht."
    )
    assert not zuviel_im_text, (
        f"{code}: Die Spezifikation verlangt {zuviel_im_text}, der Code prueft es nicht "
        "— genau die Abweichung aus K05-1/K05-2. Entweder in `core` aufnehmen "
        "(Katalogaenderung → Fassung 2027.1) oder aus der Zeile streichen."
    )
