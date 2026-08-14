"""Der Bericht sagt zuerst, wogegen er misst.

Bewertungslogik 2026.2, § 7: „Der Bericht nennt die Klasse im ersten Absatz.
Der Leser muss erkennen, dass sein Geschäft verstanden wurde, bevor er die
Punktzahl sieht. Das ist bei einem Akquisekanal wichtiger als jedes
Einzelkriterium."
"""
from types import SimpleNamespace

from services.widget_report import _einordnung, render_report_page


def _audit(**felder):
    grund = {
        "id": 1, "website_url": "https://example.de", "company_name": "Beispiel",
        "total_score": 72, "level": "Homepage Standard Silber", "coverage": 100,
        "item_scores": "{}", "item_sources": "{}", "blockers": "[]",
        "top_issues": "[]", "recommendations": "[]", "ai_summary": "",
        "erkannte_branche": "", "branchenklasse": "", "standard_version": "2026.2",
        "created_at": None,
    }
    grund.update(felder)
    return SimpleNamespace(**grund)


def test_ein_betrieb_liest_seine_branche_und_den_massstab():
    text = _einordnung(_audit(erkannte_branche="Steuerberatung",
                              branchenklasse="K2"))

    assert "Steuerberatung" in text
    assert "Beratungs- und Gesundheitsdienstleister" in text


def test_eine_seite_ohne_betrieb_erfaehrt_warum_kriterien_fehlen():
    text = _einordnung(_audit(erkannte_branche="politischer Kandidat",
                              branchenklasse="K6"))

    assert "politischer Kandidat" in text
    assert "auf Betriebe zugeschnitten" in text
    assert "zählen nicht mit" in text


def test_ohne_einordnung_bleibt_die_zeile_weg():
    """Lieber nichts sagen als eine leere Behauptung aufstellen."""
    assert _einordnung(_audit()) == ""


def test_ein_altbestand_ohne_klasse_nennt_wenigstens_die_branche():
    text = _einordnung(_audit(erkannte_branche="Dachdecker"))

    assert "Dachdecker" in text


def test_die_einordnung_steht_vor_der_punktzahl():
    seite = render_report_page(
        _audit(erkannte_branche="Dachdecker", branchenklasse="K1"),
        company="Dach Meier")

    assert "Dachdecker" in seite
    assert seite.index("Dachdecker") < seite.index("/100")
