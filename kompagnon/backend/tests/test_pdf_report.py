"""
PDF-Bericht auf Basis des überarbeiteten Kriterienkatalogs.

Der Generator war auf die früheren sechs Kategorien verdrahtet und verteilte
den Kategorie-Score proportional auf die Einzelkriterien — die Zeilenwerte im
PDF waren gerechnet, nicht gemessen. Diese Tests halten fest, dass beides
behoben bleibt.
"""
import json

import pytest

from services.audit_criteria import CATALOGUE, Source, all_criteria
from services.pdf_generator import (
    KatalogFehlt,
    _get_styles,
    build_scorecard,
    generate_audit_report,
)


def _volle_bewertung():
    items = {c.key: c.max_points for c in all_criteria()}
    sources = {c.key: Source.MEASURED.value for c in all_criteria()}
    return items, sources


def _zellentext(zelle):
    return getattr(zelle, "text", str(zelle))


# ── Bewertungsmatrix ──────────────────────────────────────────────────

def test_matrix_enthaelt_alle_kategorien_des_katalogs():
    items, sources = _volle_bewertung()
    _, rows = build_scorecard(items, sources, _get_styles())

    text = " ".join(_zellentext(z) for zeile in rows for z in zeile)
    for kategorie in CATALOGUE:
        assert kategorie.label in text, f"{kategorie.label} fehlt im PDF"


def test_matrix_hat_eine_zeile_je_kriterium():
    items, sources = _volle_bewertung()
    _, rows = build_scorecard(items, sources, _get_styles())

    # je Kategorie eine Kopfzeile plus je Kriterium eine Zeile
    assert len(rows) == len(CATALOGUE) + len(all_criteria())


def test_zeilenwerte_stammen_aus_der_einzelbewertung():
    """Der alte Generator hat den Kategorie-Score proportional verteilt."""
    items, sources = _volle_bewertung()
    items["rc_impressum"] = 3        # Teilpunktzahl, 6 wären möglich
    items["rc_datenschutz"] = 6

    _, rows = build_scorecard(items, sources, _get_styles())
    werte = {z[0]: z[4] for z in rows if isinstance(z[0], str) and z[0].startswith("RC-")}

    assert werte["RC-01"] == "3"
    assert werte["RC-02"] == "6"


def test_nicht_erhobene_kriterien_erscheinen_als_strich():
    items, sources = _volle_bewertung()
    sources["tp_inp"] = Source.NOT_COLLECTED.value
    items["tp_inp"] = 0

    _, rows = build_scorecard(items, sources, _get_styles())
    zeile = next(z for z in rows if isinstance(z[0], str) and z[0] == "TP-03")

    assert zeile[4] == "–"
    assert zeile[5] == "nicht erhoben"


def test_nicht_erhobene_kriterien_senken_das_kategorie_maximum():
    """Sonst sähe eine fehlende Messung im PDF wie ein Punktverlust aus."""
    items, sources = _volle_bewertung()
    sources["tp_inp"] = Source.NOT_COLLECTED.value
    items["tp_inp"] = 0

    _, rows = build_scorecard(items, sources, _get_styles())
    kopf = next(_zellentext(z[4]) for z in rows
                if "Performance" in _zellentext(z[0]))

    assert "13" in kopf   # 15 Punkte minus die 2 von INP


def test_quellenangabe_steht_in_jeder_zeile():
    items, sources = _volle_bewertung()
    sources["dg_aktualitaet"] = Source.AI.value

    _, rows = build_scorecard(items, sources, _get_styles())
    zeile = next(z for z in rows if isinstance(z[0], str) and z[0] == "DG-01")

    assert zeile[2] == "KI"


# ── Gesamtdokument ────────────────────────────────────────────────────

@pytest.fixture
def audit_daten():
    items, sources = _volle_bewertung()
    return {
        "total_score": 100, "level": "Homepage Standard Platin", "coverage": 100,
        "company_name": "Muster GmbH", "website_url": "https://muster.de",
        "trade": "Heizung", "city": "Bochum", "created_at": None,
        "ai_summary": "Sehr gute Website.",
        "top_issues": json.dumps(["Kein Problem gefunden"]),
        "recommendations": json.dumps(["Weiter so"]),
        "item_scores": json.dumps(items),
        "item_sources": json.dumps(sources),
        "category_scores": json.dumps([
            {"key": c.key, "label": c.label, "score": c.max_points,
             "max": c.max_points, "nominal_max": c.max_points, "not_collected": []}
            for c in CATALOGUE
        ]),
        "blockers": json.dumps([]),
    }


def test_pdf_wird_erzeugt(audit_daten):
    pdf = generate_audit_report(audit_daten)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 20_000


def test_pdf_mit_blockern_wird_erzeugt(audit_daten):
    audit_daten["blockers"] = json.dumps(["kein_impressum", "tracking_ohne_consent"])
    pdf = generate_audit_report(audit_daten)
    assert pdf.startswith(b"%PDF")


def test_altbestand_wird_abgelehnt_statt_nullen_zu_drucken():
    """Audits aus dem früheren Katalog haben keine Einzelwerte."""
    with pytest.raises(KatalogFehlt):
        generate_audit_report({"total_score": 46, "level": "Nicht konform",
                               "company_name": "Alt GmbH"})
