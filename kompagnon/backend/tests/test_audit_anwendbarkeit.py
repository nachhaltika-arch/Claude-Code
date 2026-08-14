"""Welche Kriterien für welche Branchenklasse überhaupt gelten.

Bewertungslogik 2026.2, § 2.4. Ein Kriterium, das für eine Klasse nicht gilt,
ist nicht schlecht erfüllt — es gilt nicht. Es fällt deshalb aus Zähler *und*
Nenner, wie eine nicht erhobene Messung, und wird im Bericht anders benannt:
„gilt für diese Branche nicht" statt „konnte nicht geprüft werden".
"""
import pytest

from services.audit_criteria import (
    TOTAL_POINTS,
    Source,
    anwendbares_maximum,
    find_criterion,
    ist_anwendbar,
)

# Setzen einen Betrieb voraus, der über die Seite Kunden gewinnen will.
BETRIEBSKRITERIEN = (
    "cv_klarheit", "cv_cta", "cv_kontakt", "cv_vertrauen", "cv_angebot",
    "ih_leistungsseiten", "ih_textqualitaet",
)


# ── Die Achsen des Katalogs ───────────────────────────────────────────

@pytest.mark.parametrize("key", BETRIEBSKRITERIEN)
def test_die_betriebskriterien_sind_im_katalog_markiert(key):
    assert find_criterion(key).assumes_business is True, key


def test_die_lokale_achse_haengt_allein_an_den_lokalen_signalen():
    assert find_criterion("se_lokal").assumes_local is True
    assert find_criterion("se_meta").assumes_local is False


@pytest.mark.parametrize("key", ("dg_typografie", "dg_farbsystem",
                                 "dg_bildqualitaet", "dg_aktualitaet", "dg_mobil"))
def test_gestaltung_setzt_nichts_voraus(key):
    """Typografie und Kontrast gelten für jede Seite — auch ohne Betrieb."""
    assert find_criterion(key).assumes_business is False, key
    assert ist_anwendbar(key, "K6") is True, key


# ── Anwendbarkeit je Klasse ───────────────────────────────────────────

@pytest.mark.parametrize("klasse", ("K1", "K2", "K3", "K5"))
def test_die_lokalen_klassen_bewerten_den_ganzen_katalog(klasse):
    assert anwendbares_maximum(klasse) == TOTAL_POINTS


def test_ohne_einzugsgebiet_entfallen_die_lokalen_signale():
    """K4 arbeitet bundesweit — ein Ortsbezug ist dort kein Qualitätsmerkmal."""
    assert ist_anwendbar("se_lokal", "K4") is False
    assert anwendbares_maximum("K4") == TOTAL_POINTS - 3


@pytest.mark.parametrize("key", BETRIEBSKRITERIEN)
def test_ohne_betrieb_entfallen_die_angebotskriterien(key):
    assert ist_anwendbar(key, "K6") is False, key


def test_ohne_betrieb_entfallen_auch_die_lokalen_signale():
    assert ist_anwendbar("se_lokal", "K6") is False


def test_das_anwendbare_maximum_der_klasse_ohne_betrieb():
    """Nicht anwendbar: se_lokal (3) + fünf Conversion-Kriterien (15)
    + eigene Leistungsseiten (2) + Textqualität (2) = 22 Punkte.

    Das Dokument nennt an dieser Stelle 21 Punkte und ein Maximum von 79; die
    eigenen Einzelwerte des Dokuments ergeben aber 22 und 78. Gerechnet wird
    aus dem Katalog, nicht aus der Tabelle — sonst hinge die Bewertung an einer
    Zahl, die niemand nachrechnet.
    """
    assert anwendbares_maximum("K6") == TOTAL_POINTS - 22
    assert anwendbares_maximum("K6") == 78


def test_recht_und_sicherheit_gelten_immer():
    for klasse in ("K1", "K2", "K3", "K4", "K5", "K6"):
        for key in ("rc_impressum", "rc_datenschutz", "si_ssl", "tp_lcp",
                    "bf_kontrast", "se_meta", "ih_aktualitaet"):
            assert ist_anwendbar(key, klasse) is True, f"{key}/{klasse}"


def test_eine_unbekannte_klasse_bewertet_alles():
    """Lieber vollständig bewerten als stillschweigend Kriterien verschlucken."""
    assert anwendbares_maximum("K9") == TOTAL_POINTS
    assert ist_anwendbar("cv_angebot", "K9") is True


# ── Die eigene Quelle im Bericht ──────────────────────────────────────

def test_nicht_anwendbar_ist_eine_eigene_quelle():
    """Sonst liest der Empfänger „nicht erhoben" und hält es für einen Ausfall."""
    assert Source.NOT_APPLICABLE.value == "nicht_anwendbar"
    assert Source.NOT_APPLICABLE != Source.NOT_COLLECTED
