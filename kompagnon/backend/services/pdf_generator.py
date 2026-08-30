"""
PDF Audit Report Generator — Homepage Standard 2025
Generates a professional multi-page PDF using ReportLab.

**Aufgeteilt am 2026-08-30 (L-25), nach Zustaendigkeit in drei Teile:**
`pdf_bausteine.py` traegt Farben, Stile und Tabellenhelfer,
`pdf_bericht_seiten.py` die neun Seiten, und diese Datei setzt zusammen und
baut. Sie war vorher 905 Zeilen, davon 574 in **einer** Funktion.

Sie bleibt die Adresse, unter der Router und Tests den Bericht holen — die
Namen werden hier weitergereicht, damit der Schnitt niemanden zwingt, seinen
Import zu aendern.
"""
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

# **Weitergereicht, nicht neu definiert.** 45 Fundstellen und ein Dutzend
# Tests holen diese Namen seit jeher von hier; der Schnitt vom 30.08.2026 soll
# keinen davon zwingen, seinen Import zu aendern.
from services.pdf_bausteine import (  # noqa: F401  (weitergereicht)
    BASE_TABLE_STYLE, LEGAL_COL_WIDTHS, LEGAL_ROWS, SOURCE_LABELS,
    SOURCE_SHORT, _marken_band, _category_table_style, _stil_ohne_kopfzeile,
    _stufen_abzeichen,
    FONT_BOLD, FONT_NORMAL, KC_BORDER, KC_DANGER, KC_DARK, KC_LIGHT, KC_MID,
    KC_SUCCESS, KC_TEXT_60, KC_WARNING, KC_WHITE, KC_YELLOW, KatalogFehlt,
    STATUS_ERFUELLT, STATUS_FARBEN, STATUS_OFFEN,
    STATUS_UNBEKANNT, STATUS_ZEICHEN, _clean_text, _footer, _get_styles,
    _parse_json_field, _register_fonts, _safe, _score_status, _status_color,
    branche_fuer_protokoll, build_scorecard, generate_donut_chart,
    generate_radar_chart, geo_pruefpunkte, radar_beschriftung,
    rechtstabelle_zellen, roadmap_massnahmen,
)
from services.pdf_bericht_seiten import (
    seite_befunde, seite_deckblatt, seite_diagramme, seite_geo,
    seite_protokoll, seite_recht, seite_roadmap, seite_scorecard,
    seite_zertifikat,
)


def generate_audit_report(audit_data: dict) -> bytes:
    """Generate a professional PDF audit report. Returns PDF bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    styles = _get_styles()
    story = []

    total = audit_data.get("total_score", 0) or 0
    level = _clean_text(audit_data.get("level", "Nicht konform") or "Nicht konform")
    company = _clean_text(audit_data.get("company_name", "Unbekannt") or "Unbekannt")
    url = _clean_text(audit_data.get("website_url", "") or "")
    trade = _clean_text(audit_data.get("trade", "") or "")
    city = _clean_text(audit_data.get("city", "") or "")
    created = audit_data.get("created_at", None)
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except (ValueError, TypeError):
            created = datetime.utcnow()
    elif not created:
        created = datetime.utcnow()
    date_str = created.strftime("%d.%m.%Y")
    doc.kc_jahr = created.year  # die Fusszeile datiert sich danach

    items = _parse_json_field(audit_data.get("item_scores")) or {}
    sources = _parse_json_field(audit_data.get("item_sources")) or {}
    categories = _parse_json_field(audit_data.get("category_scores")) or []
    blocker_keys = _parse_json_field(audit_data.get("blockers")) or []
    coverage = audit_data.get("coverage")

    if not isinstance(items, dict) or not items:
        # Ältere Audits haben nur die sechs Altspalten, deren Werte überwiegend
        # geschätzt waren. Ein PDF daraus wäre irreführend.
        raise KatalogFehlt(
            "Dieses Audit stammt aus dem früheren Katalog und enthält keine "
            "Einzelbewertungen. Bitte die Analyse neu ausführen."
        )
    if not isinstance(sources, dict):
        sources = {}

    top_issues = [_clean_text(i) for i in _parse_json_field(audit_data.get("top_issues"))]
    recommendations = [_clean_text(r) for r in _parse_json_field(audit_data.get("recommendations"))]
    ai_summary = _clean_text(audit_data.get("ai_summary", "") or "")

    # **Die Seiten in ihrer Reihenfolge.** Jede gibt ihre Flowables zurueck;
    # keine schreibt in eine gemeinsame Liste. Wer eine Seite verschiebt,
    # verschiebt genau eine Zeile — und `test_pdf_unveraendert` sagt sofort,
    # ob sich dabei der Inhalt geaendert hat.
    story = [
        *seite_deckblatt(styles=styles, total=total, level=level,
                         company=company, url=url, date_str=date_str,
                         created=created),
        *seite_recht(styles=styles),
        *seite_scorecard(styles=styles, total=total, level=level, items=items,
                         sources=sources, blocker_keys=blocker_keys,
                         coverage=coverage, audit_data=audit_data),
        *seite_protokoll(styles=styles, total=total, company=company, url=url,
                         city=city, date_str=date_str, categories=categories,
                         audit_data=audit_data),
        *seite_diagramme(categories=categories, audit_data=audit_data),
        *seite_befunde(styles=styles, top_issues=top_issues,
                       recommendations=recommendations, ai_summary=ai_summary),
        *seite_geo(styles=styles, audit_data=audit_data),
        *seite_roadmap(styles=styles, level=level, items=items,
                       audit_data=audit_data),
        *seite_zertifikat(styles=styles, total=total, level=level, url=url,
                          date_str=date_str),
    ]

    # Build PDF
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
