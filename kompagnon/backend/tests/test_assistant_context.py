"""Was der Assistent überhaupt zu sehen bekommt.

Entscheidung 3.4 aus `docs/projekt-assistent-anforderungen.md`: Für jeden Modus
ist explizit aufgeführt, welche Felder in den Kontext geladen werden — alles
andere erreicht das Modell nie. Der Grund steht dort auch: Marge, Stundensatz,
KI-Kosten und interne Notizen hängen am selben `Project`-Datensatz wie die
Angaben, die der Kunde sehen darf. Eine Prompt-Anweisung ist keine Grenze.

Diese Tests sind die Grenze.
"""
import pytest

from services.assistant_context import (
    MODUS_KUNDE,
    MODUS_TEAM,
    baue_kontext,
    modus_fuer_rolle,
)


class _Lead:
    company_name = "Heizung Meier GmbH"
    city = "Koblenz"
    trade = "SHK"
    email = "kontakt@meier.example"
    phone = "0261 123456"
    # Nichts davon gehört in einen Kundenkontext:
    lead_score = 87
    notizen = "Kunde zahlt schlecht, Vorkasse verlangen"


class _Briefing:
    gewerk = "Sanitär, Heizung, Klima"
    leistungen = "Wärmepumpe, Bad-Sanierung"
    einzugsgebiet = "Koblenz, 50 km"
    usp = "Meisterbetrieb seit 1974"
    mitbewerber = "Müller GmbH"
    vorbilder = "beispiel.de"
    farben = "blau"
    wunschseiten = "Start, Leistungen"
    stil = "bodenständig"
    hauptziel = "Anfragen"
    aktionen = "Anruf"
    typischer_kunde = "Hausbesitzer 55+"
    haeufige_anfrage = "Wärmepumpe"


class _Projekt:
    id = 7
    status = "phase_3"
    # Kaufmännisches — nie im Kundenkontext:
    fixed_price = 2000.0
    hourly_rate = 45.0
    actual_hours = 12.5
    ai_tool_costs = 50.0
    margin_percent = 42.0


# Feldnamen statt Zahlen: „50" steht auch in „Koblenz, 50 km" und damit
# völlig zu Recht im Kontext. Geprüft wird, dass die kaufmännischen Felder gar
# nicht erst auftauchen — mit ihnen können auch ihre Werte nicht auftauchen.
GEHEIM = ("fixed_price", "hourly_rate", "actual_hours", "ai_tool_costs",
          "margin_percent", "lead_score", "notizen", "zahlt schlecht")


def _als_text(kontext) -> str:
    import json
    return json.dumps(kontext, ensure_ascii=False, default=str)


# ── Der Modus kommt aus der Rolle, nicht vom Client ──────────────────────

@pytest.mark.parametrize("rolle,erwartet", [
    ("kunde", MODUS_KUNDE),
    ("admin", MODUS_TEAM),
    ("superadmin", MODUS_TEAM),
])
def test_die_rolle_bestimmt_den_modus(rolle, erwartet):
    assert modus_fuer_rolle(rolle) == erwartet


@pytest.mark.parametrize("rolle", ["auditor", "nutzer", "", None, "erfunden"])
def test_eine_unklare_rolle_bekommt_den_engeren_modus(rolle):
    """`auditor` ist im Backend nicht abgegrenzt (§ 2.1 der Anforderungen). Bis
    das entschieden ist, gilt die restriktivere Sicht — nicht die großzügigere."""
    assert modus_fuer_rolle(rolle) == MODUS_KUNDE


# ── Was der Kunde sieht ──────────────────────────────────────────────────

def test_der_kunde_sieht_sein_briefing():
    kontext = baue_kontext(MODUS_KUNDE, lead=_Lead(), briefing=_Briefing(),
                           projekt=_Projekt())

    assert kontext["betrieb"]["firma"] == "Heizung Meier GmbH"
    assert kontext["briefing"]["gewerk"] == "Sanitär, Heizung, Klima"
    assert kontext["projekt"]["status"] == "phase_3"


@pytest.mark.parametrize("geheim", GEHEIM)
def test_kein_kaufmaennisches_feld_erreicht_den_kundenkontext(geheim):
    text = _als_text(baue_kontext(MODUS_KUNDE, lead=_Lead(), briefing=_Briefing(),
                                  projekt=_Projekt()))
    assert geheim not in text


def test_auch_die_werte_selbst_fehlen():
    """Gegenprobe mit einem Wert, der nirgends sonst vorkommen kann."""
    class _Auffaellig:
        id = 1
        status = "phase_1"
        margin_percent = 41.777

    assert "41.777" not in _als_text(baue_kontext(MODUS_KUNDE, projekt=_Auffaellig()))


def test_interne_notizen_erreichen_den_kunden_nie():
    kontext = baue_kontext(MODUS_KUNDE, lead=_Lead(), briefing=_Briefing())
    assert "notizen" not in _als_text(kontext)


# ── Was das Team sieht ───────────────────────────────────────────────────

def test_das_team_sieht_die_kennzahlen():
    kontext = baue_kontext(MODUS_TEAM, lead=_Lead(), briefing=_Briefing(),
                           projekt=_Projekt())

    assert kontext["projekt"]["margin_percent"] == 42.0
    assert kontext["projekt"]["actual_hours"] == 12.5


def test_auch_das_team_bekommt_nur_freigegebene_felder():
    """Die Liste ist auch hier eine Liste — nur eine längere."""
    class _MitGeheimnis:
        id = 1
        status = "phase_1"
        api_schluessel = "sk-geheim-123"

    kontext = baue_kontext(MODUS_TEAM, projekt=_MitGeheimnis())

    assert "sk-geheim-123" not in _als_text(kontext)


# ── Die eigentliche Eigenschaft: neue Felder sind unsichtbar ─────────────

def test_ein_neues_feld_am_projekt_ist_standardmaessig_unsichtbar():
    """Das ist der Kern von 3.4: Wer morgen eine Spalte `deckungsbeitrag`
    ergänzt, hat sie nicht versehentlich im Kundenkontext."""
    class _Morgen:
        id = 1
        status = "phase_2"
        deckungsbeitrag = 1234.56

    text = _als_text(baue_kontext(MODUS_KUNDE, projekt=_Morgen()))

    assert "1234.56" not in text
    assert "deckungsbeitrag" not in text


def test_ohne_daten_entsteht_ein_leerer_aber_gueltiger_kontext():
    kontext = baue_kontext(MODUS_KUNDE)

    assert kontext["betrieb"] == {}
    assert kontext["briefing"] == {}
    assert kontext["projekt"] == {}


def test_ein_unbekannter_modus_wird_abgewiesen():
    """Lieber ein Fehler als versehentlich die weite Sicht."""
    with pytest.raises(ValueError):
        baue_kontext("chef", lead=_Lead())


# ── Leere Briefing-Felder ────────────────────────────────────────────────

def test_leere_felder_stehen_nicht_im_kontext():
    """Sonst füllt sich der Prompt mit `null` und das Modell hält Leeres für
    beantwortet."""
    class _Halb:
        gewerk = "Elektro"
        leistungen = ""
        einzugsgebiet = None

    kontext = baue_kontext(MODUS_KUNDE, briefing=_Halb())

    assert kontext["briefing"] == {"gewerk": "Elektro"}


def test_offene_felder_werden_benannt():
    """Der Assistent soll wissen, was noch fehlt — das ist seine Hauptaufgabe."""
    class _Halb:
        gewerk = "Elektro"
        leistungen = ""

    kontext = baue_kontext(MODUS_KUNDE, briefing=_Halb())

    assert "leistungen" in kontext["briefing_offen"]
    assert "gewerk" not in kontext["briefing_offen"]
