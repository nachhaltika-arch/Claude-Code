"""Der Name, mit dem der Empfänger angesprochen wird.

Der Bericht aus dem Widget ist ein Akquise-Mittel: er wird von jemandem
gelesen, der uns nicht kennt. „Analyse für gordonbeyer.de" ist dabei schwächer
als „Analyse für Gordon Beyer" — aber „Analyse für Startseite" wäre schlechter
als beides. Der Titel einer Seite taugt also nur mit Prüfung als Firmenname.
"""
import pytest

from services.scraper import firmenname_aus_titel, firmenname_fuer_audit


@pytest.mark.parametrize("titel,erwartet", [
    ("Dachdeckerei Meier", "Dachdeckerei Meier"),
    ("Dachdeckerei Meier – Ihr Dach in guten Händen", "Dachdeckerei Meier"),
    ("Heizung Krause | Wärmepumpe und Bad", "Heizung Krause"),
    ("Gordon Beyer - Bürgermeisterkandidat für Templin", "Gordon Beyer"),
])
def test_ein_echter_name_bleibt_erhalten(titel, erwartet):
    assert firmenname_aus_titel(titel) == erwartet


@pytest.mark.parametrize("titel", [
    "Startseite", "startseite", "  Start  ", "Home", "HOME",
    "Willkommen", "Herzlich willkommen", "Index", "Website", "Webseite",
    "Neue Seite", "Unbenanntes Dokument", "",
])
def test_ein_platzhaltertitel_gilt_nicht_als_firmenname(titel):
    """Sonst steht „Startseite" im Bericht und in der Anrede der Mail."""
    assert firmenname_aus_titel(titel) == ""


def test_der_platzhalter_vor_dem_trenner_faellt_ebenfalls_durch():
    """„Home | Dachdeckerei Meier" darf nicht zu „Home" werden."""
    assert firmenname_aus_titel("Home | Dachdeckerei Meier") == ""


def test_ein_einzelnes_zeichen_ist_kein_name():
    assert firmenname_aus_titel("-") == ""
    assert firmenname_aus_titel("A") == ""


def test_der_name_wird_begrenzt():
    assert len(firmenname_aus_titel("X" * 300)) == 100


# ── Die Rückfallkette des Audits ──────────────────────────────────────

def test_ein_angegebener_name_hat_vorrang():
    assert firmenname_fuer_audit(
        "Dachdeckerei Meier GmbH", "Dachdeckerei Meier",
        "https://meier-dach.de") == "Dachdeckerei Meier GmbH"


def test_ohne_angabe_gilt_der_gefundene_name():
    assert firmenname_fuer_audit(
        "", "Gordon Beyer", "https://gordonbeyer.de") == "Gordon Beyer"


def test_ohne_namen_bleibt_die_domain_uebrig_nicht_die_volle_adresse():
    """Vorher stand im Bericht „https://gordonbeyer.de/" statt der Domain."""
    assert firmenname_fuer_audit(
        "", "", "https://www.gordonbeyer.de/kontakt") == "gordonbeyer.de"


def test_leerzeichen_zaehlen_nicht_als_angabe():
    assert firmenname_fuer_audit(
        "   ", "Gordon Beyer", "https://gordonbeyer.de") == "Gordon Beyer"
