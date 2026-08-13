"""Stufe C: die Abfolge einer Seite.

Geprüft wird, was vor dem ersten Zeichen Markup entschieden wird — welche
Sections in welcher Reihenfolge. Kein Token fließt: `ki_runde` wird ersetzt.
"""
import pytest

from services.page_composer import (
    KompositionsAbbruch,
    baue_prompt,
    komponiere,
    pruefe_komposition,
)

BLOECKE = [
    {"slug": "hero-standard", "category": "HERO", "name": "Hero Standard",
     "ki_prompt_hint": "Startseite, klares Versprechen"},
    {"slug": "leist-grid-3", "category": "LEIST", "name": "Leistungen 3er-Grid",
     "ki_prompt_hint": ""},
    {"slug": "trust-logos", "category": "TRUST", "name": "Logo-Streifen"},
    {"slug": "cta-angebot", "category": "CTA", "name": "Angebot anfordern"},
]
ERLAUBT = {b["slug"] for b in BLOECKE}


class _Antwort:
    content = []


def _runden(*ergebnisse):
    folge = iter(ergebnisse)
    aufrufe = []

    def ki_runde(client, nachrichten):
        aufrufe.append(list(nachrichten))
        return _Antwort(), next(folge)

    return ki_runde, aufrufe


def _abfolge(*slugs):
    return {"aufbau": "Vom Versprechen zum Termin.",
            "sections": [{"slug": s, "rolle": "Rolle", "auftrag": "Ein Satz."}
                         for s in slugs]}


# ── Was an einer Abfolge falsch sein kann ────────────────────────────────

def test_eine_saubere_abfolge_hat_nichts_offen():
    sections = _abfolge("hero-standard", "leist-grid-3", "cta-angebot")["sections"]
    assert pruefe_komposition(sections, ERLAUBT) == []


def test_ein_erfundener_block_wird_beanstandet():
    sections = _abfolge("hero-standard", "gibt-es-nicht")["sections"]

    verstoesse = pruefe_komposition(sections, ERLAUBT)

    assert any(v["regel"] == "C1" for v in verstoesse)
    assert "gibt-es-nicht" in verstoesse[0]["text"]


def test_derselbe_block_zweimal_hintereinander_ist_keine_seite():
    """Genau das ist der Unterschied zwischen Komponieren und Aneinanderreihen."""
    sections = _abfolge("hero-standard", "leist-grid-3", "leist-grid-3")["sections"]

    assert any(v["regel"] == "C2" for v in pruefe_komposition(sections, ERLAUBT))


def test_derselbe_block_mit_abstand_ist_erlaubt():
    """Ein zweiter CTA weiter unten ist gewollt — die Spec verlangt ihn sogar."""
    sections = _abfolge("cta-angebot", "leist-grid-3", "cta-angebot")["sections"]

    assert pruefe_komposition(sections, ERLAUBT) == []


def test_eine_leere_abfolge_ist_ein_verstoss():
    assert pruefe_komposition([], ERLAUBT)[0]["regel"] == "C0"


# ── Der Auftrag ──────────────────────────────────────────────────────────

def test_eine_saubere_abfolge_braucht_keine_zweite_runde():
    ki_runde, aufrufe = _runden(_abfolge("hero-standard", "leist-grid-3"))

    ergebnis = komponiere(ki_runde=ki_runde, client=None, seite="Startseite",
                          zweck="", ist_startseite=True, briefing=None,
                          bloecke=BLOECKE)

    assert ergebnis["contract"]["konform"] is True
    assert [s["slug"] for s in ergebnis["sections"]] == ["hero-standard", "leist-grid-3"]
    assert ergebnis["aufbau"] == "Vom Versprechen zum Termin."
    assert len(aufrufe) == 1


def test_ein_erfundener_block_geht_einmal_zurueck():
    ki_runde, aufrufe = _runden(_abfolge("hero-standard", "erfunden"),
                                _abfolge("hero-standard", "leist-grid-3"))

    ergebnis = komponiere(ki_runde=ki_runde, client=None, seite="Startseite",
                          zweck="", ist_startseite=True, briefing=None,
                          bloecke=BLOECKE)

    assert ergebnis["contract"]["konform"] is True
    assert len(aufrufe) == 2
    assert "erfunden" in aufrufe[1][-1]["content"]


def test_eine_schlechtere_nachbesserung_wird_nicht_uebernommen():
    ki_runde, _ = _runden(_abfolge("hero-standard", "erfunden"),
                          _abfolge("erfunden", "auch-erfunden", "auch-erfunden"))

    ergebnis = komponiere(ki_runde=ki_runde, client=None, seite="Startseite",
                          zweck="", ist_startseite=True, briefing=None,
                          bloecke=BLOECKE)

    assert [s["slug"] for s in ergebnis["sections"]] == ["hero-standard", "erfunden"]
    assert ergebnis["contract"]["konform"] is False


def test_ohne_bibliothek_gibt_es_nichts_zu_komponieren():
    ki_runde, _ = _runden(_abfolge("hero-standard"))

    with pytest.raises(KompositionsAbbruch):
        komponiere(ki_runde=ki_runde, client=None, seite="Startseite", zweck="",
                   ist_startseite=True, briefing=None, bloecke=[])


def test_eine_antwort_ohne_sections_bricht_ab():
    ki_runde, _ = _runden({"aufbau": "leer"})

    with pytest.raises(KompositionsAbbruch):
        komponiere(ki_runde=ki_runde, client=None, seite="Startseite", zweck="",
                   ist_startseite=True, briefing=None, bloecke=BLOECKE)


# ── Der Auftrag ans Modell ───────────────────────────────────────────────

class _Briefing:
    gewerk = "Sanitär, Heizung, Klima"
    leistungen = "Wärmepumpe, Bad-Sanierung"
    einzugsgebiet = "Koblenz"
    usp = "Meisterbetrieb seit 1974"
    stil = None
    sonstige_hinweise = None


def test_der_prompt_nennt_die_pflicht_sections_der_startseite():
    prompt = baue_prompt(seite="Startseite", zweck="Erstkontakt", ist_startseite=True,
                         briefing=_Briefing(), bloecke=BLOECKE)

    assert "PFLICHT-SECTIONS" in prompt
    assert "Garantie" in prompt and "Dringlichkeit" in prompt
    assert "Meisterbetrieb seit 1974" in prompt
    # Nur die erlaubten Blöcke stehen drin.
    assert "hero-standard" in prompt and "gibt-es-nicht" not in prompt


def test_auf_einer_unterseite_sind_die_sections_eine_empfehlung():
    prompt = baue_prompt(seite="Über uns", zweck="Vertrauen", ist_startseite=False,
                         briefing=None, bloecke=BLOECKE)

    assert "PFLICHT-SECTIONS" not in prompt
    assert "üblich" in prompt


def test_die_bestehende_abfolge_steht_im_auftrag():
    """Verbessern ist etwas anderes als bei null anfangen."""
    prompt = baue_prompt(seite="Startseite", zweck="", ist_startseite=True,
                         briefing=None, bloecke=BLOECKE,
                         bestehend=["hero-standard", "cta-angebot"])

    assert "verbessere sie" in prompt
    assert "- hero-standard" in prompt
