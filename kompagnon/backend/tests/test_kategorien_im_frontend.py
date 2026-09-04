"""Das Frontend kennt genau die acht Kategorien des Katalogs (S6.5).

**Der Verdacht.** § 9 Punkt 3 der Bewertungslogik fuehrt als Pruefpunkt, ob
das Frontend noch den alten Katalog mit sechs Kategorien zeigt. `AuditReport.jsx`
traegt tatsaechlich eine fest verdrahtete Liste — sie ist aber der **Rueckfallweg**
fuer Audits von vor dem 11.08.2026, die den Katalog noch nicht mitliefern.
Neue Audits werden aus `audit.catalogue` gezeichnet.

**Entwarnung, mit einer Bedingung.** Der Rueckfallweg stimmt nur, solange
`CATEGORY_META` jede Kategorie des Katalogs kennt. Fehlt ein Schluessel, faellt
die Darstellung still auf Standardfarbe und Langtext zurueck — kein Fehler, den
irgendetwas meldet, nur eine Kategorie, die anders aussieht als die sieben
anderen. Deshalb dieser Test.
"""
import re
from pathlib import Path

from services.audit_criteria import CATALOGUE

#: **Seit dem 30.08.2026 in `audit/auditDaten.jsx`.** `AuditReport.jsx` stand
#: mit 1.025 Zeilen ueber der Groessengrenze und ist geteilt (L-25); die
#: Kataloge sind mit ausgezogen. Dieser Test hat den Umzug gemeldet —
#: „CATEGORY_META nicht gefunden — wurde das Bauteil umgebaut?", und genau
#: das war passiert. Die Frage im Text war die richtige.
BAUTEIL = (Path(__file__).resolve().parents[2] / "frontend" / "src"
           / "components" / "audit" / "auditDaten.jsx")


def _meta_schluessel() -> set:
    text = BAUTEIL.read_text(encoding="utf-8")
    block = re.search(r"const CATEGORY_META = \{(.*?)\n\};", text, re.S)
    assert block, "CATEGORY_META nicht gefunden — wurde das Bauteil umgebaut?"
    return set(re.findall(r"^\s*(\w+):\s*\{", block.group(1), re.M))


def test_jede_kategorie_des_katalogs_hat_darstellungsangaben():
    # Arrange
    katalog = {c.key for c in CATALOGUE}

    # Act
    frontend = _meta_schluessel()

    # Assert
    assert katalog <= frontend, (
        f"Ohne Angaben im Frontend: {sorted(katalog - frontend)}. Diese "
        "Kategorien erscheinen in Standardfarbe und mit dem Langtext als "
        "Kurzform — sichtbar anders als die uebrigen, ohne dass etwas meldet."
    )


def test_das_frontend_erfindet_keine_kategorie_dazu():
    """Gegenprobe: ein Schluessel im Frontend, den der Katalog nicht kennt.

    Er waere tote Darstellung — und ein Hinweis darauf, dass eine Kategorie
    aus dem Katalog entfernt, im Frontend aber vergessen wurde.
    """
    # Arrange
    katalog = {c.key for c in CATALOGUE}

    # Act
    ueberzaehlig = _meta_schluessel() - katalog

    # Assert
    assert not ueberzaehlig, f"Kennt der Katalog nicht: {sorted(ueberzaehlig)}"


def test_es_sind_acht():
    """Die Zahl steht im Buch. Sie muss aus dem Katalog folgen, nicht daneben."""
    assert len(CATALOGUE) == 8
