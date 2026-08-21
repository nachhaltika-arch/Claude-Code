"""
Tests für den Audit-Kriterienkatalog und die Score-Normierung.

Der Katalog ist die einzige Wahrheitsquelle für Kategorien, Punkte und
Erhebungsart — diese Tests halten ihn konsistent, wenn die Gewichtung
später angepasst wird.
"""
import pytest

from services.audit_criteria import (
    CATALOGUE,
    INFRASTRUCTURE,
    TOTAL_POINTS,
    Source,
    ai_criteria,
    all_criteria,
    determine_level,
    find_criterion,
    item_keys,
    score_all,
    ERWARTETE_GESAMTPUNKTE,
)


# ── Katalog-Konsistenz ────────────────────────────────────────────────

def test_die_gesamtpunktzahl_ist_die_erklaerte():
    """Nicht „100", sondern „die Zahl, die jemand hingeschrieben hat".

    Der Test verlangte bis zum 21.08.2026 exakt 100 — und widersprach damit
    dem Kopf von `audit_criteria.py`, der sagt, dass die Gewichte nicht auf
    100 aufgehen muessen, weil normiert wird. Beides konnte nicht stimmen.

    Jetzt haelt er, was er halten soll: Eine **versehentliche** Verschiebung
    faellt weiterhin auf; eine beabsichtigte muss in
    `ERWARTETE_GESAMTPUNKTE` eingetragen werden, mit Datum und Grund.
    """
    assert TOTAL_POINTS == ERWARTETE_GESAMTPUNKTE


def test_kategorie_maximum_entspricht_summe_ihrer_kriterien():
    """Verhindert den alten Deckel-Bug: 6 Kriterien à 1 Punkt bei max 5."""
    for category in CATALOGUE:
        assert category.max_points == sum(c.max_points for c in category.criteria)


def test_kriterien_schluessel_sind_eindeutig():
    keys = item_keys()
    assert len(keys) == len(set(keys))


def test_jedes_bewertete_kriterium_hat_punkte():
    for criterion in all_criteria():
        assert criterion.max_points > 0


def test_infrastruktur_zaehlt_nicht_in_den_score():
    for criterion in INFRASTRUCTURE:
        assert criterion.max_points == 0


def test_backup_kriterium_ist_entfallen():
    """Von außen nicht prüfbar — darf nicht zurückkommen."""
    assert find_criterion("ho_backup") is None


def test_design_und_conversion_sind_im_katalog():
    keys = {c.key for c in CATALOGUE}
    assert "design" in keys
    assert "conversion" in keys


def test_hoechstens_ein_fuenftel_wird_von_der_ki_bewertet():
    ki_punkte = sum(c.max_points for c in ai_criteria())
    assert ki_punkte <= 20, f"{ki_punkte} Punkte KI-bewertet — zu viel geschätzt"


# ── Normierung ────────────────────────────────────────────────────────

def _volle_punktzahl():
    items = {c.key: c.max_points for c in all_criteria()}
    sources = {c.key: Source.MEASURED for c in all_criteria()}
    return items, sources


def test_volle_punktzahl_ergibt_hundert():
    items, sources = _volle_punktzahl()
    assert score_all(items, sources)["total_score"] == 100


def test_null_punkte_ergibt_null():
    _, sources = _volle_punktzahl()
    items = {c.key: 0 for c in all_criteria()}
    assert score_all(items, sources)["total_score"] == 0


def test_nicht_erhobene_kriterien_senken_den_score_nicht():
    """Eine fehlende Messung darf nicht als 'null Punkte' durchschlagen."""
    items, sources = _volle_punktzahl()
    for key in ("tp_lcp", "tp_cls", "tp_inp", "tp_mobile"):
        items[key] = 0
        sources[key] = Source.NOT_COLLECTED

    result = score_all(items, sources)
    assert result["total_score"] == 100
    assert result["possible_points"] < TOTAL_POINTS
    assert result["coverage"] < 100


def test_abdeckung_meldet_wie_viel_geprueft_wurde():
    items, sources = _volle_punktzahl()
    for criterion in all_criteria():
        if criterion.key.startswith("dg_"):
            sources[criterion.key] = Source.NOT_COLLECTED

    result = score_all(items, sources)
    assert result["coverage"] == 90  # Design = 10 von 100 Punkten


def test_alles_nicht_erhoben_ergibt_null_statt_absturz():
    items = {c.key: 0 for c in all_criteria()}
    sources = {c.key: Source.NOT_COLLECTED for c in all_criteria()}
    result = score_all(items, sources)
    assert result["total_score"] == 0
    assert result["possible_points"] == 0


def test_punkte_werden_auf_das_kriterien_maximum_begrenzt():
    items, sources = _volle_punktzahl()
    items["rc_impressum"] = 999
    result = score_all(items, sources)
    assert result["total_score"] == 100


# ── Level und K.-o.-Kriterien ─────────────────────────────────────────

@pytest.mark.parametrize("score,erwartet", [
    (100, "Homepage Standard Platin"),
    (95, "Homepage Standard Platin"),
    (85, "Homepage Standard Gold"),
    (70, "Homepage Standard Silber"),
    (50, "Homepage Standard Bronze"),
    (49, "Nicht konform"),
    (0, "Nicht konform"),
])
def test_level_schwellen(score, erwartet):
    assert determine_level(score) == erwartet


def test_fehlendes_impressum_deckelt_auf_nicht_konform():
    """Ohne Impressum darf kein Gütesiegel vergeben werden."""
    assert determine_level(92, ["kein_impressum"]) == "Nicht konform"


def test_fehlende_datenschutzerklaerung_deckelt_auf_nicht_konform():
    assert determine_level(88, ["keine_datenschutzerklaerung"]) == "Nicht konform"


def test_ungueltiges_tls_deckelt_auf_nicht_konform():
    assert determine_level(96, ["kein_gueltiges_tls"]) == "Nicht konform"


def test_tracking_ohne_consent_deckelt_auf_bronze():
    assert determine_level(96, ["tracking_ohne_consent"]) == "Homepage Standard Bronze"


def test_deckel_verschlechtert_ein_ohnehin_schlechtes_level_nicht():
    assert determine_level(20, ["tracking_ohne_consent"]) == "Nicht konform"


def test_ohne_blocker_bleibt_das_level_unveraendert():
    assert determine_level(96, []) == "Homepage Standard Platin"
