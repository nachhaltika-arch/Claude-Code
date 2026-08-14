"""Der Maßstab je Branchenklasse.

Bewertungslogik 2026.2, § 3. Für jede Klasse ist festgelegt, *wogegen*
gemessen wird. Die Zeile, die das ganze Branchenmodell trägt, steht bei C5:
Eine Steuerkanzlei ohne Preisrahmen ist nicht schlechter, sondern
berufsrechtlich korrekt.
"""
import pytest

from services.audit_criteria import find_criterion
from services.audit_industry_map import KLASSEN
from services.audit_industry_profiles import (
    KI_KRITERIEN_MIT_PROFIL,
    massstab_fuer,
    rubric_fuer_prompt,
)

ALLE_KLASSEN = ("K1", "K2", "K3", "K4", "K5", "K6")


# ── Vollständigkeit ───────────────────────────────────────────────────

@pytest.mark.parametrize("klasse", ("K1", "K2", "K3", "K4", "K5"))
@pytest.mark.parametrize("kriterium", ("cv_klarheit", "cv_cta", "cv_kontakt",
                                       "cv_vertrauen", "cv_angebot",
                                       "se_meta", "se_schema", "ih_leistungsseiten"))
def test_jede_betriebsklasse_hat_zu_jedem_kriterium_einen_massstab(klasse, kriterium):
    assert massstab_fuer(kriterium, klasse), f"{kriterium}/{klasse}"


def test_die_klassen_stimmen_mit_der_zuordnung_ueberein():
    """Sonst kennt die Zuordnung eine Klasse, für die es keinen Maßstab gibt."""
    for klasse in KLASSEN:
        if klasse != "K6":
            assert massstab_fuer("cv_angebot", klasse), klasse


def test_die_kriterien_mit_profil_gibt_es_auch_im_katalog():
    for key in KI_KRITERIEN_MIT_PROFIL:
        assert find_criterion(key) is not None, key


# ── Die Zeile, um die es geht ─────────────────────────────────────────

def test_bei_beratungsberufen_werden_preise_nicht_erwartet():
    massstab = massstab_fuer("cv_angebot", "K2")

    assert "nicht erwartet" in massstab.lower()
    assert "preis" in massstab.lower()


def test_beim_leistungsbetrieb_gehoert_der_preisrahmen_dazu():
    assert "preisrahmen" in massstab_fuer("cv_angebot", "K1").lower()


def test_der_ueberregionale_anbieter_wird_nicht_am_ort_gemessen():
    massstab = massstab_fuer("se_meta", "K4").lower()

    assert "ort" in massstab
    assert "nicht erwartet" in massstab


# ── Was in den Prompt geht ────────────────────────────────────────────

def test_der_prompt_teil_nennt_klasse_und_massstab():
    text = rubric_fuer_prompt("K2")

    assert "K2" in text
    assert KLASSEN["K2"].bezeichnung in text
    assert "cv_angebot" in text


def test_der_prompt_teil_enthaelt_nur_die_ki_kriterien():
    """Für gemessene Kriterien entscheidet der Code, nicht das Modell."""
    text = rubric_fuer_prompt("K1")

    assert "cv_klarheit" in text
    assert "cv_angebot" in text
    # cv_kontakt wird gemessen — sein Maßstab hat im Prompt nichts zu suchen.
    assert "cv_kontakt" not in text


def test_ohne_betrieb_bleibt_der_prompt_teil_leer():
    """Bei K6 gilt keines der angebotsbezogenen Kriterien."""
    assert rubric_fuer_prompt("K6").strip() == ""


def test_eine_unbekannte_klasse_liefert_keinen_massstab_statt_eines_falschen():
    assert massstab_fuer("cv_angebot", "K9") == ""
    assert rubric_fuer_prompt("K9").strip() == ""
