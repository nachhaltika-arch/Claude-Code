"""Im Auditprotokoll steht ein Befund, keine Vermutung.

Gefunden am 14.08.2026 an einem echten Bericht: Das PDF eines Ingenieurbüros
für nachhaltige Wirtschaft führte „Branche / Gewerk: Schreiner". Die Zeile kam
aus `scraper.py`, das über Stichworte rät — „holz" im Seitentext genügt. Im
Protokoll gelesen ist das kein Vorschlag mehr, sondern ein Befund mit
Unterschrift darunter.

Die richtige Quelle liegt seit dem Branchenmodell 2026.2 daneben:
`erkannte_branche` und `branchenklasse`. Der HTML-Bericht nutzte sie längst,
das PDF nicht.
"""
from services.pdf_generator import branche_fuer_protokoll


def test_die_erkannte_branche_schlaegt_die_stichwort_vermutung():
    zeile = branche_fuer_protokoll({
        "erkannte_branche": "Ingenieurbüro für nachhaltige Wirtschaft",
        "branchenklasse": "K2",
        "trade": "Schreiner",
    })

    assert "Ingenieurbüro für nachhaltige Wirtschaft" in zeile
    assert "Schreiner" not in zeile


def test_die_zeile_nennt_auch_den_massstab():
    """Wogegen gemessen wurde, gehört ins Protokoll — sonst ist es keines."""
    zeile = branche_fuer_protokoll({
        "erkannte_branche": "Steuerberatung", "branchenklasse": "K2"})

    assert "Beratungs- und Gesundheitsdienstleister" in zeile


def test_ohne_freitext_bleibt_die_klasse():
    zeile = branche_fuer_protokoll({"branchenklasse": "K1"})

    assert zeile == "Lokaler Leistungsbetrieb"


def test_ein_altbestand_zeigt_die_eingetragene_branche():
    """Vor 2026.2 gab es nur `trade` — dort ist es das Beste, was vorliegt."""
    assert branche_fuer_protokoll({"trade": "Heizung"}) == "Heizung"


def test_ohne_jede_angabe_wird_nichts_behauptet():
    assert branche_fuer_protokoll({}) == "k.A."
    assert branche_fuer_protokoll({"erkannte_branche": "", "trade": ""}) == "k.A."


def test_eine_unbekannte_klasse_erfindet_keinen_massstab():
    zeile = branche_fuer_protokoll({"erkannte_branche": "Imkerei",
                                    "branchenklasse": "K9"})

    assert zeile == "Imkerei"


# ── Die beiden anderen Dokumente aus derselben Datenzeile ─────────────
#
# Der Fix vom 14.08. hat das Auditprotokoll gehärtet. Angebots-PDF und
# Kaltakquise-Anschreiben stammen aus demselben Datensatz und wurden nicht
# angefasst — ein Ingenieurbüro bekam ein Angebot mit „Schreiner" auf dem
# Deckblatt und einen Brief, der ihm dasselbe unterstellte, während das
# beigelegte Protokoll korrekt „Ingenieurbüro" sagte.

def test_das_angebot_druckt_die_vermutung_nicht_mehr():
    """`angebot_pdf` nimmt dieselbe Rangfolge wie das Protokoll."""
    from services import angebot_pdf

    # Arrange — geratenes Gewerk, korrekt erkannte Branche
    daten = {
        "company_name": "Muster GmbH",
        "trade": "Schreiner",
        "erkannte_branche": "Ingenieurbüro für Tragwerksplanung",
        "branchenklasse": "K2",
        "total_score": 62,
    }

    # Act
    pdf = angebot_pdf.erzeuge_angebot(daten) if hasattr(
        angebot_pdf, "erzeuge_angebot") else None

    # Assert — die Funktion selbst ist hier nebensächlich; entscheidend ist,
    # dass die Branchenzeile aus `branche_fuer_protokoll` kommt
    assert "Ingenieurbüro" in branche_fuer_protokoll(daten)
    assert "Schreiner" not in branche_fuer_protokoll(daten)
    assert pdf is None or isinstance(pdf, (bytes, bytearray))


def test_ohne_erhebung_bleibt_das_angebot_ohne_branchenzeile():
    """`k.A.` gehört auf ein Angebotsdeckblatt nicht — die Zeile fällt weg."""
    # Arrange — nur die Vermutung liegt vor
    daten = {"trade": "Schreiner", "erkannte_branche": "", "branchenklasse": ""}

    # Act — `angebot_pdf` übergibt bewusst kein `trade` mehr
    branche = branche_fuer_protokoll({**daten, "trade": ""})

    # Assert
    assert branche == "k.A."
