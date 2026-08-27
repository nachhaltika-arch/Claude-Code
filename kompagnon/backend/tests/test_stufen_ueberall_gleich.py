"""Die fünf Stufen stehen an drei Stellen — und müssen überall gleich sein (S5.7).

**Befund N1, und warum ein Waechter noetig ist.** Die Schwellen standen
doppelt im Haus: Das Backend staffelte 95/85/70/50, Widget und Akquise-Haken
staffelten 85/70/50/30. Derselbe Score hiess damit im Bericht „Silber" und im
Widget „Gold" — und beides sah derselbe Betrieb.

Angeglichen wurde das von Hand. Was von Hand angeglichen wurde, laeuft wieder
auseinander; der bestehende Waechter (`test_die_gesamtpunktzahl_ist_die_
erklaerte`) prueft den Katalog **gegen sich selbst** und sieht Frontend und
Widget nicht.

**Warum ein Python-Test ueber JavaScript-Dateien.** Der Katalog ist die
Wahrheitsquelle, und er liegt hier. Ein Test auf der anderen Seite muesste
den Katalog nachbilden — und waere damit die vierte Stelle, an der dieselben
Zahlen stehen.
"""
import re
from pathlib import Path

import pytest

from services.audit_criteria import LEVELS

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
HILFSDATEI = FRONTEND / "src" / "utils" / "homepageStandard.js"
WIDGET = FRONTEND / "public" / "embed" / "audit-widget.html"


def _katalog() -> list:
    """(Schwelle, Stufenname) — absteigend, wie im Katalog."""
    return [(grenze, name) for grenze, name in LEVELS]


def _aus_der_hilfsdatei() -> list:
    text = HILFSDATEI.read_text(encoding="utf-8")
    return [(int(g), n) for g, n in
            re.findall(r"\{\s*ab:\s*(\d+),\s*name:\s*'([^']+)'", text)]


def _aus_dem_widget() -> list:
    text = WIDGET.read_text(encoding="utf-8")
    return [(int(g), n.strip()) for g, n in
            re.findall(r"if \(s >= (\d+)\) return '([^']+?)\s*[^\w\s']?';", text)]


@pytest.mark.parametrize("name, leser", [
    ("utils/homepageStandard.js", _aus_der_hilfsdatei),
    ("embed/audit-widget.html", _aus_dem_widget),
])
def test_die_schwellen_stimmen_mit_dem_katalog_ueberein(name, leser):
    # Arrange
    katalog = _katalog()

    # Act
    gefunden = leser()

    # Assert
    assert gefunden, f"In {name} keine Stufen gefunden — Aufbau geaendert?"
    # Die Null-Stufe („Nicht konform") traegt keine Schwelle: Im Widget ist
    # sie der Rueckfall ohne Vergleich, in der Hilfsdatei steht sie mit `ab: 0`.
    # Verglichen werden deshalb die echten Schwellen auf beiden Seiten.
    katalog_schwellen = [g for g, _ in katalog if g > 0]
    gefundene_schwellen = [g for g, _ in gefunden if g > 0]
    assert gefundene_schwellen == katalog_schwellen, (
        f"{name} staffelt {gefundene_schwellen}, der Katalog "
        f"{katalog_schwellen}. Derselbe Score hiesse dann an zwei Stellen "
        "verschieden — und beides sieht derselbe Betrieb."
    )


def test_auch_die_stufennamen_stimmen():
    """Eine gleiche Schwelle mit anderem Namen ist derselbe Fehler."""
    # Arrange
    namen = {n for _, n in _katalog()}

    # Act / Assert
    for quelle, gefunden in (("Hilfsdatei", _aus_der_hilfsdatei()),
                             ("Widget", _aus_dem_widget())):
        fremd = [n for _, n in gefunden if n not in namen]
        assert not fremd, f"{quelle} nennt Stufen, die der Katalog nicht kennt: {fremd}"
