"""Was neben einem Kriterium steht, gilt für die Branche des Lesers.

Bewertungslogik 2026.2, § 3: Der Maßstab je Branchenklasse steht in
`audit_industry_profiles`. Er stand dort bisher nur für das Modell — der
Bericht zeigte weiter den allgemeinen Hinweis aus dem Katalog. Ein
Ingenieurbüro las deshalb neben „Eigene Leistungsseiten", es solle „je Gewerk
eine Seite" führen, und neben „Vertrauenssignale" den Meisterbetrieb.

Das ist derselbe Fehler wie der Kandidatenauftritt vom 14.08.2026, nur eine
Ebene tiefer: Die Punktzahl passt zur Branche, der Text daneben nicht.
"""
from types import SimpleNamespace

from services.widget_report import _hinweis, render_report_page
from services.audit_criteria import find_criterion


def _audit(**felder):
    grund = {
        "id": 1, "website_url": "https://example.de", "company_name": "Beispiel",
        "total_score": 52, "level": "Homepage Standard Bronze", "coverage": 96,
        "item_scores": "{}", "item_sources": "{}", "blockers": "[]",
        "top_issues": "[]", "recommendations": "[]", "ai_summary": "",
        "erkannte_branche": "", "branchenklasse": "", "standard_version": "2026.2",
        "created_at": None,
    }
    grund.update(felder)
    return SimpleNamespace(**grund)


def test_ein_ingenieurbuero_liest_seinen_eigenen_massstab():
    crit = find_criterion("ih_leistungsseiten")

    assert "Fachgebiet" in _hinweis(crit, "K2")
    assert "Gewerk" not in _hinweis(crit, "K2")


def test_ein_handwerksbetrieb_liest_weiter_den_handwerklichen_massstab():
    """Die Neutralisierung darf K1 nicht die Schärfe nehmen."""
    assert "Gewerk" in _hinweis(find_criterion("ih_leistungsseiten"), "K1")


def test_ohne_klassenmassstab_bleibt_der_katalog_hinweis():
    crit = find_criterion("se_index")

    assert _hinweis(crit, "K2") == crit.hint


def test_ein_altbestand_ohne_klasse_faellt_auf_den_katalog_zurueck():
    crit = find_criterion("ih_leistungsseiten")

    assert _hinweis(crit, "") == crit.hint


def test_der_katalog_hinweis_unterstellt_kein_gewerk():
    """Der Rückfall trifft jede Branche — er darf keine voraussetzen."""
    for key in ("ih_leistungsseiten", "cv_vertrauen"):
        hint = find_criterion(key).hint.lower()
        assert "gewerk" not in hint
        assert "meisterbetrieb" not in hint


def test_der_bericht_eines_ingenieurbueros_nennt_keinen_meisterbetrieb():
    seite = render_report_page(
        _audit(erkannte_branche="Ingenieurbüro für nachhaltige Wirtschaft",
               branchenklasse="K2"),
        company="Nachhaltika")

    assert "Meisterbetrieb" not in seite
    assert "je Gewerk" not in seite
