"""Sieht der Auditbericht nach einem Umbau noch gleich aus? (L-25)

**Warum es diesen Test gibt.** `generate_audit_report` hat 576 Zeilen — zwei
Drittel von `pdf_generator.py` — und steht seit dem 22.08.2026 auf der Liste
zum Zerlegen. Der Eintrag L-25 hat es bewusst **nicht** getan, mit einer
klaren Begründung: Die dreissig vorhandenen Tests prüfen Bausteine („wird
erzeugt", Matrixlogik), aber **ob das PDF danach noch gleich aussieht, sagt
keiner**. Der Bericht geht an Kunden.

Dieser Test ist die Gegenprobe, die davor gehört. Er hält den **Textinhalt in
seiner Reihenfolge** fest — abgegriffen an `SimpleDocTemplate.build`, also
dort, wo der Bericht fertig ist und das Zeichnen beginnt (`tests/pdf_inhalt`).

**Was er kann und was nicht.** Er sieht Text, Reihenfolge und Tabellenzellen.
Er sieht **kein** Layout — Schriftgrößen, Abstände, Farben stehen in den
Stilen, nicht im Text. Ein Umbau, der nur Text und Reihenfolge erhält, kann
das PDF trotzdem hässlich machen. Die Sichtprüfung eines erzeugten PDF
ersetzt er nicht; er verhindert nur, dass man sie *jedes Mal* braucht.

**Wenn er rot wird**, ist das zuerst eine Frage und kein Fehler: Hat der
Umbau den Inhalt verändert, oder war die Änderung gewollt? Ist sie gewollt,
wird die Grundlage neu geschrieben — bewusst und in einem eigenen Commit:

    ./venv/bin/python -m pytest tests/test_pdf_unveraendert.py --grundlage-neu
"""
import json
import pathlib
from datetime import datetime

import pytest

from pdf_inhalt import inhalt_von
from services.audit_criteria import CATALOGUE, Source, all_criteria
from services.pdf_generator import generate_audit_report

GRUNDLAGE = pathlib.Path(__file__).parent / "daten" / "auditbericht_inhalt.txt"

#: Ein festes Datum, damit die Grundlage nicht jeden Tag eine andere ist.
AUDITDATUM = datetime(2026, 1, 15)


def _audit_daten(blocker: list = None) -> dict:
    items = {c.key: c.max_points for c in all_criteria()}
    sources = {c.key: Source.MEASURED.value for c in all_criteria()}
    return {
        "total_score": 100, "level": "Homepage Standard Platin", "coverage": 100,
        "company_name": "Muster GmbH", "website_url": "https://muster.de",
        "trade": "Heizung", "city": "Bochum", "created_at": AUDITDATUM,
        "ai_summary": "Sehr gute Website.",
        "top_issues": json.dumps(["Kein Problem gefunden"]),
        "recommendations": json.dumps(["Weiter so"]),
        "item_scores": json.dumps(items),
        "item_sources": json.dumps(sources),
        "category_scores": json.dumps([
            {"key": c.key, "label": c.label, "score": c.max_points,
             "max": c.max_points, "nominal_max": c.max_points,
             "not_collected": []}
            for c in CATALOGUE
        ]),
        "blockers": json.dumps(blocker or []),
    }


def test_der_inhalt_ist_zwischen_zwei_laeufen_gleich():
    """Vorbedingung: Ohne das wäre die Grundlage wertlos."""
    # Arrange
    daten = _audit_daten()

    # Act
    erster = inhalt_von(generate_audit_report, daten)
    zweiter = inhalt_von(generate_audit_report, daten)

    # Assert
    assert erster == zweiter


def test_der_bericht_hat_denselben_inhalt_wie_zuvor(request):
    # Arrange
    daten = _audit_daten()

    # Act
    jetzt = inhalt_von(generate_audit_report, daten)

    if request.config.getoption("--grundlage-neu"):
        GRUNDLAGE.write_text("\n".join(jetzt), encoding="utf-8")
        pytest.skip(f"Grundlage neu geschrieben: {len(jetzt)} Textstuecke")

    # Assert
    assert GRUNDLAGE.exists(), (
        f"Keine Grundlage unter {GRUNDLAGE}. Einmal mit --grundlage-neu laufen."
    )
    vorher = GRUNDLAGE.read_text(encoding="utf-8").split("\n")

    if vorher != jetzt:
        nur_vorher = [z for z in vorher if z not in jetzt][:5]
        nur_jetzt = [z for z in jetzt if z not in vorher][:5]
        pytest.fail(
            "Der Auditbericht hat einen anderen Inhalt als zuvor "
            f"({len(vorher)} → {len(jetzt)} Textstuecke).\n"
            f"  nicht mehr da: {nur_vorher}\n"
            f"  neu:           {nur_jetzt}\n"
            "War das gewollt? Dann --grundlage-neu, in einem eigenen Commit."
        )


def test_ein_blocker_aendert_den_inhalt_sichtbar():
    """Gegenprobe: Ein Waechter, der nie anschlaegt, ist wertlos."""
    # Arrange & Act
    ohne = inhalt_von(generate_audit_report, _audit_daten())
    mit = inhalt_von(generate_audit_report,
                     _audit_daten(["kein_impressum", "tracking_ohne_consent"]))

    # Assert
    assert ohne != mit, (
        "Ein Blocker schlaegt sich nicht im Textinhalt nieder — dann wuerde "
        "dieser Test einen Umbau auch nicht bemerken."
    )
