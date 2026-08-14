"""Die Bewertung läuft gegen den Maßstab der erkannten Klasse.

Bewertungslogik 2026.2, § 2.3 und § 10 Schritt 4. Darin steckt ein
Widerspruch, der aufgelöst werden muss: Der Maßstab hängt an der Klasse, die
Klasse an der Erkennung — und die Erkennung passierte bisher in demselben
Aufruf, der den Maßstab schon braucht. Das Modell darf seinen Maßstab aber
nicht selbst wählen. Also wird zuerst erkannt, dann zugeordnet, dann bewertet.

Kein Test hier ruft ein Modell auf.
"""
import pytest

from services import audit_ai


def _als_text(inhalt) -> str:
    """Der Bewertungsaufruf schickt Blöcke, der Erkennungsaufruf blanken Text."""
    if isinstance(inhalt, str):
        return inhalt
    return "\n".join(teil.get("text", "") for teil in inhalt
                     if isinstance(teil, dict))


@pytest.fixture
def modellaufrufe(monkeypatch):
    """Fängt beide Modellaufrufe ab und merkt sich, was sie geschickt haben."""
    aufrufe = []

    def _antwort(*, systemprompt, inhalt, schema, max_tokens, modell,
                 effort="medium"):
        aufrufe.append({"systemprompt": systemprompt, "inhalt": _als_text(inhalt),
                        "modell": modell, "effort": effort})
        if "branche" in schema["properties"] and len(schema["properties"]) <= 3:
            return {"branche": "Steuerberatung mit Schwerpunkt Handwerk",
                    "betriebsseite": True}
        return {"cv_klarheit": 2, "cv_angebot": 2, "ih_textqualitaet": 1,
                "dg_aktualitaet": 2, "dg_typografie": 2, "dg_farbsystem": 2,
                "dg_bildqualitaet": 1, "dg_mobil": 1,
                "begruendung": "…", "ai_summary": "…",
                "top_issues": [], "recommendations": []}

    monkeypatch.setattr(audit_ai, "_ruf_modell", _antwort)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest")
    return aufrufe


FAKTEN = {"company_name": "Kanzlei Meier", "trade": "", "city": "Kassel",
          "url": "https://example.de", "page_text": "Steuerberatung"}


def test_die_erkennung_laeuft_vor_der_bewertung(modellaufrufe):
    audit_ai.evaluate(FAKTEN)

    assert len(modellaufrufe) == 2, "erst erkennen, dann bewerten"


def test_der_bewertungsprompt_traegt_den_massstab_der_klasse(modellaufrufe):
    audit_ai.evaluate(FAKTEN)

    bewertung = modellaufrufe[1]["inhalt"]
    assert "K2" in bewertung
    # Die Zeile, um die es beim ganzen Branchenmodell geht.
    assert "NICHT erwartet: Preisangaben" in bewertung


def test_der_erkennungsprompt_traegt_keinen_massstab(modellaufrufe):
    """Sonst wählt das Modell seinen Maßstab doch selbst."""
    audit_ai.evaluate(FAKTEN)

    erkennung = modellaufrufe[0]["inhalt"]
    assert "NICHT erwartet: Preisangaben" not in erkennung
    assert "K2" not in erkennung


def test_das_ergebnis_traegt_klasse_und_herkunft(modellaufrufe):
    ergebnis = audit_ai.evaluate(FAKTEN)

    assert ergebnis["branche"] == "Steuerberatung mit Schwerpunkt Handwerk"
    assert ergebnis["betriebsseite"] is True
    assert ergebnis["branchenklasse"] == "K2"
    assert ergebnis["branchenklasse_quelle"] == "map"


def test_ohne_erkennung_wird_nicht_bewertet(monkeypatch):
    """Ohne Klasse gäbe es nur den alten festen Maßstab — lieber nichts."""
    monkeypatch.setattr(audit_ai, "_ruf_modell", lambda **kw: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest")

    assert audit_ai.evaluate(FAKTEN) == {}


def test_scheitert_die_bewertung_bleibt_die_erkennung_erhalten(monkeypatch):
    """Die Klasse allein ist schon etwas wert: Sie erklärt dem Leser den Rahmen."""
    aufrufe = {"n": 0}

    def _antwort(**kw):
        aufrufe["n"] += 1
        if aufrufe["n"] == 1:
            return {"branche": "Dachdecker", "betriebsseite": True}
        return None

    monkeypatch.setattr(audit_ai, "_ruf_modell", _antwort)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest")

    ergebnis = audit_ai.evaluate(FAKTEN)

    assert ergebnis["branchenklasse"] == "K1"
    assert "cv_angebot" not in ergebnis


def test_bei_einer_seite_ohne_betrieb_bleibt_der_massstab_leer(monkeypatch):
    def _antwort(*, systemprompt, inhalt, schema, max_tokens, modell,
                 effort="medium"):
        if "branche" in schema["properties"] and len(schema["properties"]) <= 3:
            return {"branche": "politischer Kandidat", "betriebsseite": False}
        assert "MASZSTAB DIESER BRANCHENKLASSE" not in inhalt
        return {"dg_typografie": 2, "begruendung": "…", "ai_summary": "…",
                "top_issues": [], "recommendations": []}

    monkeypatch.setattr(audit_ai, "_ruf_modell", _antwort)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest")

    ergebnis = audit_ai.evaluate(FAKTEN)

    assert ergebnis["branchenklasse"] == "K6"
    assert ergebnis["betriebsseite"] is False
