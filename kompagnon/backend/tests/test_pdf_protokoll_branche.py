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
