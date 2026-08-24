"""Was das Modell nicht beurteilen kann, kostet keine Punkte (S8.1).

**Der Widerspruch.** Der Bewertungsprompt sagte: „Wenn du etwas nicht
beurteilen kannst, vergib 0 Punkte." § 3.5 der Bewertungslogik sagt das
Gegenteil: Was nicht erhoben wurde, faellt aus Zaehler **und** Nenner. Ein
Betrieb verlor damit bis zu neun Punkte fuer etwas, das er nicht getan hat —
und im Bericht stand es als Einschaetzung ueber ihn, nicht als Luecke der
Pruefung.

**Es war nicht nur der Satz.** Das JSON-Schema erzwang fuer jedes
KI-Kriterium `integer` und fuehrte alle als `required`. Das Modell **konnte**
nichts anderes als eine Zahl liefern, selbst wenn es gewollt haette. Eine
Prompt-Aenderung allein waere wirkungslos geblieben — der haeufigste Fehler
bei genau dieser Art Reparatur.

**Warum eine eigene Liste und kein `null`.** Ein Vereinigungstyp im Schema
haengt davon ab, welchen Schema-Dialekt die Schnittstelle akzeptiert; das
liesse sich ohne Schluessel nicht pruefen. Eine Liste von Kennungen ist in
jedem Dialekt gueltig — und sie zwingt das Modell, das Nichtbeurteilbare zu
**benennen**, statt es wegzulassen.
"""
from services.audit_ai import _schema
from services.audit_criteria import Source, ai_criteria
from services.audit_scoring import score_audit


def test_das_schema_laesst_nichtbeurteilbares_zu():
    # Arrange / Act
    schema = _schema()

    # Assert
    assert "nicht_beurteilbar" in schema["properties"], (
        "Ohne dieses Feld kann das Modell nur Zahlen liefern — auch fuer "
        "das, was es nicht gesehen hat."
    )
    assert schema["properties"]["nicht_beurteilbar"]["type"] == "array"


def test_der_prompt_verlangt_keine_null_punkte_mehr():
    from services.audit_ai import SYSTEM_PROMPT

    # Assert
    assert "vergib 0 Punkte" not in SYSTEM_PROMPT, (
        "Der Satz widerspricht § 3.5 der Bewertungslogik."
    )
    assert "nicht_beurteilbar" in SYSTEM_PROMPT


def test_benanntes_kriterium_faellt_aus_der_wertung():
    # Arrange
    erstes = ai_criteria()[0].key
    zweites = ai_criteria()[1].key
    ki = {c.key: c.max_points for c in ai_criteria()}
    ki["nicht_beurteilbar"] = [erstes]

    # Act
    ergebnis = score_audit({}, ki)

    # Assert
    assert ergebnis["sources"][erstes] == Source.NOT_COLLECTED.value
    assert ergebnis["sources"][zweites] == Source.AI.value, (
        "Nur das benannte Kriterium faellt heraus, nicht die ganze Gruppe."
    )


def test_eine_null_bleibt_eine_null():
    """Gegenprobe: 0 Punkte sind weiterhin eine gueltige Bewertung.

    „Nicht beurteilbar" und „schlecht" duerfen nicht dasselbe werden — sonst
    verschwindet jede echte Null aus der Wertung.
    """
    # Arrange
    erstes = ai_criteria()[0].key
    ki = {c.key: 0 for c in ai_criteria()}
    ki["nicht_beurteilbar"] = []

    # Act
    ergebnis = score_audit({}, ki)

    # Assert
    assert ergebnis["sources"][erstes] == Source.AI.value
    assert ergebnis["items"][erstes] == 0


def test_unbekannte_kennung_in_der_liste_stoert_nicht():
    """Das Modell koennte etwas benennen, das kein Kriterium ist."""
    # Arrange
    ki = {c.key: 1 for c in ai_criteria()}
    ki["nicht_beurteilbar"] = ["gibt_es_nicht"]

    # Act / Assert — kein Fehler, und die echten Kriterien bleiben bewertet.
    ergebnis = score_audit({}, ki)
    assert ergebnis["sources"][ai_criteria()[0].key] == Source.AI.value
