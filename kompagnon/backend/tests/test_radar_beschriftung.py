"""
Die Achsen des Netzdiagramms brauchen kurze Namen.

Die Beschriftung wurde mit ``label.split(" &")[0]`` gekürzt. Das trifft sieben
der acht Kategorien — „Barrierefreiheit (WCAG/BFSG)" führt kein „&" und stand
deshalb als einzige in voller Länge am Diagrammrand, breiter als die halbe
Grafik.

Der Name der Kategorie ist der Teil vor der ersten Klammer oder Konjunktion.
"""
from services.pdf_generator import generate_radar_chart, radar_beschriftung


# Die acht Kategorien des Katalogs, wie sie in `audit_criteria` heißen
KATEGORIEN = [
    ("Recht & Compliance", "Recht"),
    ("Sicherheit & Datenschutz", "Sicherheit"),
    ("Performance & Core Web Vitals", "Performance"),
    ("Barrierefreiheit (WCAG/BFSG)", "Barrierefreiheit"),
    ("SEO & Auffindbarkeit", "SEO"),
    ("Design & Gestaltung", "Design"),
    ("Conversion & Nutzerführung", "Conversion"),
    ("Inhalt & Substanz", "Inhalt"),
]


def test_jede_kategorie_wird_auf_ihren_namen_gekuerzt():
    for voll, kurz in KATEGORIEN:
        assert radar_beschriftung(voll) == kurz


def test_keine_beschriftung_wird_zu_lang():
    # Arrange — mehr als das sprengt bei acht Achsen die Grafik
    for voll, _ in KATEGORIEN:
        assert len(radar_beschriftung(voll)) <= 18, voll


def test_ein_name_ohne_zusatz_bleibt_stehen():
    assert radar_beschriftung("Inhalt") == "Inhalt"


def test_leere_beschriftung_bleibt_leer():
    assert radar_beschriftung("") == ""


# ── Das Diagramm selbst ────────────────────────────────────────────

def test_das_diagramm_entsteht_fuer_den_vollen_katalog():
    # Arrange
    achsen = [(kurz, 5.0) for _, kurz in KATEGORIEN]

    # Act
    png = generate_radar_chart(achsen)

    # Assert
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_das_diagramm_haelt_randfaelle_aus():
    # Arrange & Act — ohne Achsen und mit einer einzigen; die Wahl des
    # Beschriftungswinkels rechnet über Nachbarn und darf hier nicht scheitern
    for achsen in ([], [("Nur eine", 0.0)]):
        png = generate_radar_chart(achsen)

        # Assert
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
