"""Der Ortsname im Auditprotokoll steht ganz da.

Gefunden am 14.08.2026 im PDF eines echten Berichts: „Stadt: Boppard-". Das
Muster ließ nach dem Bindestrich nur Kleinbuchstaben zu und brach deshalb an
jedem zusammengesetzten Ortsnamen ab. Ein abgeschnittener Ort im Protokoll
liest sich wie ein Tippfehler in einem Dokument, das Sorgfalt verkauft.
"""
import pytest

from services.scraper import stadt_aus_text


@pytest.mark.parametrize("text,erwartet", [
    ("Musterstraße 1, 56154 Boppard-Buchholz", "Boppard-Buchholz"),
    ("56154 Boppard", "Boppard"),
    ("61348 Bad Homburg", "Bad Homburg"),
    ("06108 Halle-Neustadt", "Halle-Neustadt"),
])
def test_zusammengesetzte_ortsnamen_bleiben_ganz(text, erwartet):
    assert stadt_aus_text(text) == erwartet


def test_ein_ort_endet_nie_auf_einem_bindestrich():
    assert not stadt_aus_text("56154 Boppard-Buchholz").endswith("-")


def test_ohne_postleitzahl_wird_nichts_geraten():
    assert stadt_aus_text("Wir arbeiten bundesweit.") == ""
