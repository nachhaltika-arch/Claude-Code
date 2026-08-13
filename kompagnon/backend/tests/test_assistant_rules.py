"""Der Maßstab für Briefing-Antworten.

Entscheidung 3.3: explizite Regeln statt „das Modell wird es schon merken".
Was sich zählen lässt, prüft der Code — das spart einen Aufruf je leerem Feld
und macht die Bewertung nachvollziehbar.
"""
import pytest

from services.assistant_rules import (
    NACH_FELD,
    REGELN,
    pruefe_antwort,
    regelwerk_fuer_prompt,
)


# ── Was der Code allein erkennt ──────────────────────────────────────────

def test_ein_leeres_feld_kostet_keinen_ki_aufruf():
    befund = pruefe_antwort("leistungen", "")

    assert befund.brauchbar is False
    assert "Noch nichts eingetragen" in befund.als_text
    # Die Frage steht dabei — sonst weiß der Nutzer nicht, was gemeint ist.
    assert "Was genau wird angeboten" in befund.als_text


def test_eine_konkrete_antwort_geht_durch():
    befund = pruefe_antwort(
        "leistungen",
        "Wärmepumpen (Luft/Wasser), Bad-Sanierung barrierefrei, "
        "Heizungswartung, 24h-Notdienst")

    assert befund.brauchbar is True
    assert befund.hinweise == []


def test_zu_knapp_wird_benannt_und_mit_beispiel_beantwortet():
    befund = pruefe_antwort("leistungen", "Heizung")

    assert befund.brauchbar is False
    assert "knapp" in befund.als_text
    # Ein Beispiel hilft mehr als eine Rüge.
    assert "Wärmepumpen" in befund.als_text


@pytest.mark.parametrize("floskel", [
    "Alles rund ums Wasser und mehr, seit vielen Jahren für Sie im Einsatz",
    "Kompetent und zuverlässig — Ihr Partner für Bad und Heizung im Kreis",
    "Wir bieten höchste Qualität und modernste Technik für jeden Auftrag",
])
def test_floskeln_werden_erkannt(floskel):
    befund = pruefe_antwort("usp", floskel)

    assert befund.brauchbar is False
    assert "jeden anderen auch" in befund.als_text


def test_die_floskel_wird_zitiert_statt_nur_geruegt():
    befund = pruefe_antwort("usp", "Wir arbeiten kompetent und zuverlässig, "
                                   "damit Sie sich wohlfühlen im neuen Bad")

    assert "kompetent und zuverlässig" in befund.als_text


def test_ein_unbekanntes_feld_wird_nicht_bewertet():
    """Der Assistent behauptet nichts über Felder, für die es keinen Maßstab gibt."""
    befund = pruefe_antwort("lieblingsfarbe", "grün")

    assert befund.brauchbar is True
    assert befund.hinweise == []


def test_ein_unbekanntes_feld_ohne_inhalt_bleibt_unbrauchbar():
    assert pruefe_antwort("lieblingsfarbe", "").brauchbar is False


# ── Das Regelwerk selbst ─────────────────────────────────────────────────

def test_jede_regel_hat_ein_gutes_und_ein_schlechtes_beispiel():
    for regel in REGELN:
        assert regel.gut and regel.schlecht, regel.feld
        assert regel.gut != regel.schlecht


def test_die_guten_beispiele_bestehen_die_eigene_pruefung():
    """Ein Maßstab, den das eigene Beispiel nicht besteht, ist kein Maßstab.

    Dieselbe Lehre wie beim Block-Vertrag: erst am Bestand messen.
    """
    for regel in REGELN:
        befund = pruefe_antwort(regel.feld, regel.gut)
        assert befund.brauchbar, f"{regel.feld}: {befund.als_text}"


def test_die_schlechten_beispiele_fallen_durch():
    """Sonst prüft die Regel nichts."""
    for regel in REGELN:
        befund = pruefe_antwort(regel.feld, regel.schlecht)
        assert not befund.brauchbar, f"{regel.feld} lässt „{regel.schlecht}“ durch"


def test_der_prompt_teil_nennt_feld_frage_und_beide_beispiele():
    text = regelwerk_fuer_prompt(["usp"])

    assert "usp" in text
    assert "Meisterbetrieb in dritter Generation" in text
    assert "Qualität und Service" in text
    # Wofür die Antwort gebraucht wird, gehört dazu — sonst rät das Modell.
    assert "Hero" in text


def test_ohne_auswahl_steht_das_ganze_regelwerk_im_prompt():
    text = regelwerk_fuer_prompt()

    for regel in REGELN:
        assert regel.feld in text


def test_unbekannte_felder_erzeugen_keinen_leeren_block():
    assert regelwerk_fuer_prompt(["gibt-es-nicht"]) == ""


def test_die_regeln_decken_die_briefing_felder_des_kontexts_ab():
    """Nicht jedes Feld braucht eine Regel — aber die tragenden schon."""
    tragend = {"gewerk", "leistungen", "einzugsgebiet", "usp", "hauptziel"}

    assert tragend <= set(NACH_FELD)
