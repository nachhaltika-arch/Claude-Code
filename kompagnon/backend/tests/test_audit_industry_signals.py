"""Die messbare Seite des Branchenmaßstabs.

Der Bericht sprach seit dem 14.08.2026 die Sprache der jeweiligen Klasse,
gerechnet wurde weiter handwerklich: „Eigene Leistungsseiten" suchte nach
`wärmepumpe` und `wallbox`, „Vertrauenssignale" nach `meisterbetrieb` und
`innung`. Ein Ingenieurbüro kann beides nicht haben und verlor Punkte dafür.
"""
import pytest

from services.audit_industry_map import KLASSEN
from services.audit_industry_signals import (
    _GRUPPEN,
    alle_begriffe,
    begriffe,
    treffer,
    zaehlt_in_klasse,
)


# ── Der Maßstab je Klasse ─────────────────────────────────────────────

def test_ein_handwerksbetrieb_misst_weiter_an_seinen_eigenen_begriffen():
    """Die Ausweitung darf K1 nichts wegnehmen."""
    k1 = begriffe("leistungsseiten", "K1")

    assert "wärmepumpe" in k1
    assert "meisterbetrieb" in begriffe("zertifikate", "K1")


def test_ein_beratungsbetrieb_misst_an_seinen():
    assert "gutachten" in begriffe("leistungsseiten", "K2")
    assert "kammer" in begriffe("zertifikate", "K2")


def test_der_handwerkliche_massstab_gilt_nicht_ueberall():
    assert "wärmepumpe" not in begriffe("leistungsseiten", "K2")
    assert "meisterbetrieb" not in begriffe("zertifikate", "K2")


def test_die_basis_gilt_in_jeder_klasse():
    for klasse in KLASSEN:
        assert "leistung" in begriffe("leistungsseiten", klasse)


def test_ohne_klasse_wird_grosszuegig_gezaehlt():
    """Wen wir nicht einordnen konnten, dürfen wir dafür nicht abwerten."""
    assert set(begriffe("zertifikate", "")) == set(alle_begriffe("zertifikate"))


def test_eine_unbekannte_klasse_faellt_auf_die_basis_zurueck():
    ohne = begriffe("leistungsseiten", "K9")

    assert "leistung" in ohne
    assert "wärmepumpe" not in ohne


# ── Erhebung und Bewertung greifen ineinander ─────────────────────────

def test_die_erhebung_sucht_den_verband_aller_klassen():
    """Die Klasse steht erst nach der Erhebung fest — sie muss alles finden."""
    alle = alle_begriffe("zertifikate")

    assert "meisterbetrieb" in alle
    assert "kammer" in alle
    assert "trusted shops" in alle


def test_treffer_meldet_nur_was_dasteht():
    gefunden = treffer("Wir sind Mitglied der Ingenieurkammer Rheinland-Pfalz.",
                       "zertifikate")

    assert "kammer" in gefunden
    assert "meisterbetrieb" not in gefunden


def test_ein_kammertreffer_zaehlt_beim_ingenieurbuero_und_nicht_beim_shop():
    gefunden = treffer("Mitglied der Ingenieurkammer", "zertifikate")

    assert zaehlt_in_klasse(gefunden, "zertifikate", "K2")
    assert not zaehlt_in_klasse(("meisterbetrieb",), "zertifikate", "K2")


def test_ohne_treffer_zaehlt_nichts():
    assert not zaehlt_in_klasse((), "zertifikate", "K1")
    assert not zaehlt_in_klasse(None, "cta", "K1")


# ── Was die Begriffslisten sich nicht erlauben dürfen ─────────────────

@pytest.mark.parametrize("gruppe", sorted(_GRUPPEN))
def test_kein_begriff_ist_so_kurz_dass_er_ueberall_trifft(gruppe):
    """„installation" hat im Scraper jede zweite deutsche Seite getroffen."""
    for begriff in alle_begriffe(gruppe):
        assert len(begriff) >= 3, f"{begriff!r} in {gruppe} greift zu weit"


@pytest.mark.parametrize("gruppe", sorted(_GRUPPEN))
def test_alle_begriffe_sind_kleingeschrieben(gruppe):
    """Gesucht wird in kleingeschriebenem Text — Großbuchstaben träfen nie."""
    for begriff in alle_begriffe(gruppe):
        assert begriff == begriff.lower()


@pytest.mark.parametrize("gruppe", sorted(_GRUPPEN))
def test_jede_bewertbare_klasse_hat_einen_eigenen_massstab(gruppe):
    """K6 ausgenommen — dort gilt kein angebotsbezogenes Kriterium."""
    _, je_klasse = _GRUPPEN[gruppe]
    for klasse in KLASSEN:
        if klasse == "K6":
            continue
        assert je_klasse.get(klasse), f"{klasse} fehlt in {gruppe}"
