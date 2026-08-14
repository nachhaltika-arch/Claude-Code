"""Die KI-Bewertung erkennt erst, was sie vor sich hat — dann bewertet sie.

Anlass: Der Systemprompt setzte „Websites von Handwerksbetrieben (Heizung,
Sanitär, Elektrik)" fest. Beim Auftritt eines politischen Kandidaten erkannte
das Modell die Seite richtig und rechnete sie trotzdem gegen den SHK-Maßstab —
mit fehlenden Leistungen, fehlendem Einsatzgebiet und fehlendem Preisrahmen als
Befund. Hier wird geprüft, dass die Erkennung Teil der Antwort ist und der
Maßstab am erkannten Gewerk hängt statt an einer festen Liste.
"""
from services.audit_ai import SYSTEM_PROMPT, _schema, _user_content
from services.audit_criteria import ai_criteria


def test_das_schema_verlangt_branche_und_betriebsseite():
    schema = _schema()

    assert "branche" in schema["properties"]
    assert "betriebsseite" in schema["properties"]
    assert schema["properties"]["betriebsseite"]["type"] == "boolean"
    # Beides muss kommen, sonst kann das Scoring nicht entscheiden.
    assert "branche" in schema["required"]
    assert "betriebsseite" in schema["required"]


def test_das_schema_enthaelt_weiter_alle_ki_kriterien():
    schema = _schema()

    for criterion in ai_criteria():
        assert criterion.key in schema["properties"], criterion.key
        assert criterion.key in schema["required"], criterion.key


def test_der_systemprompt_schreibt_kein_gewerk_mehr_vor():
    """Der Maßstab kommt aus der erkannten Branche, nicht aus einer Konstante."""
    tief = SYSTEM_PROMPT.lower()

    assert "wärmepumpe" not in tief
    assert "wallbox" not in tief


def test_der_systemprompt_verlangt_die_erkennung():
    tief = SYSTEM_PROMPT.lower()

    assert "branche" in tief
    assert "betriebsseite" in tief


def test_das_erkannte_gewerk_steht_im_kontext():
    inhalt = _user_content(
        {"company_name": "Dach Meier", "trade": "Dachdecker", "city": "Kassel",
         "url": "https://example.de", "page_text": "Dachsanierung"},
        {}, None)

    text = inhalt[-1]["text"]
    assert "Dachdecker" in text
