"""Wie ein Auditergebnis zur Antwort wird (L-25).

**Warum eigene Datei, 23.08.2026.** `routers/audit.py` stand bei 842 Zeilen.
Die letzten hundert davon enthalten keine einzige Route: Sie bereiten auf, was
in der Datenbank als JSON-Text liegt, damit die Oberflaeche es lesen kann —
Kriterienkatalog, Klassenbezeichnung, das fertige Auditobjekt.

Das ist eine eigene Sorte Arbeit. Wer eine Route liest, will nicht wissen,
wie `item_scores` entpackt wird; wer die Darstellung aendert, will nicht durch
zwoelf Endpunkte blaettern.

**Vor dem Schnitt geprueft, wer diese vier braucht:** `_json_field`,
`_catalogue_payload`, `_klassenbezeichnung` und `_format_audit` werden von
**keiner** anderen Datei importiert. Der gleichnamige `_json_field` in
`services/widget_report.py` ist ein eigener — die Namensgleichheit hatte den
ersten Blick in die Irre gefuehrt.
"""
import json
import logging

from database import AuditResult
from services.audit_criteria import (BLOCKER_LABELS, CATALOGUE, SOURCE_LABELS,
                                     Source)

logger = logging.getLogger(__name__)


def _json_field(raw, fallback):
    try:
        return json.loads(raw) if raw else fallback
    except (json.JSONDecodeError, TypeError):
        return fallback


def _catalogue_payload(items: dict, sources: dict) -> list:
    """Kategorien mit Kriterien, Punkten und Quellen-Kennzeichnung."""
    payload = []
    for category in CATALOGUE:
        criteria = []
        for crit in category.criteria:
            source = sources.get(crit.key, Source.NOT_COLLECTED.value)
            criteria.append({
                "key": crit.key,
                "label": crit.label,
                "hint": crit.hint,
                "max": crit.max_points,
                "score": int(items.get(crit.key, 0) or 0),
                "source": source,
                "source_label": SOURCE_LABELS.get(Source(source), source),
                "collected": source != Source.NOT_COLLECTED.value,
            })
        payload.append({
            "key": category.key,
            "label": category.label,
            "nominal_max": category.max_points,
            "criteria": criteria,
        })
    return payload


def _klassenbezeichnung(klasse: str) -> str:
    """„K2" allein sagt dem Leser nichts — die Bezeichnung gehört dazu."""
    from services.audit_industry_map import KLASSEN

    eintrag = KLASSEN.get(klasse or "")
    return eintrag.bezeichnung if eintrag else ""


def _format_audit(audit: AuditResult) -> dict:
    """Format audit for JSON response."""
    items = _json_field(getattr(audit, "item_scores", None), {})
    sources = _json_field(getattr(audit, "item_sources", None), {})
    categories = _json_field(getattr(audit, "category_scores", None), [])
    blocker_keys = _json_field(getattr(audit, "blockers", None), [])

    return {
        "id": audit.id,
        "status": audit.status,
        "lead_id": audit.lead_id,
        "website_url": audit.website_url,
        "company_name": audit.company_name,
        "contact_name": audit.contact_name,
        "city": audit.city,
        "trade": audit.trade,
        # Auto-scraped vom Impressum-Scraper in start_audit() — fürs
        # Lead-Anlegen-Modal als Prefill, sonst nirgends genutzt.
        "phone":       getattr(audit, "scraped_phone", "") or "",
        "email":       getattr(audit, "scraped_email", "") or "",
        "description": getattr(audit, "scraped_description", "") or "",
        "total_score": audit.total_score,
        "level": audit.level,
        "coverage": getattr(audit, "coverage", None),
        # Über wie viele Seiten geurteilt wurde. Ergebnisse vor dem 21.08.2026
        # kannten nur die Startseite; die Spaltenvorgabe 1 sagt das ehrlich.
        "seiten_geprueft": getattr(audit, "seiten_geprueft", None) or 1,
        "seiten_gefunden": getattr(audit, "seiten_gefunden", None),
        "collection_notes": _json_field(getattr(audit, "collection_notes", None), {}),
        # Der Maßstab, gegen den bewertet wurde — siehe Bewertungslogik 2026.2.
        "erkannte_branche": getattr(audit, "erkannte_branche", "") or "",
        "branchenklasse": getattr(audit, "branchenklasse", "") or "",
        "branchenklasse_bezeichnung": _klassenbezeichnung(
            getattr(audit, "branchenklasse", "")),
        "standard_version": getattr(audit, "standard_version", "") or "",
        "categories": categories,
        "catalogue": _catalogue_payload(items, sources),
        "items": items,
        "sources": sources,
        "blockers": [
            {"key": k, "label": BLOCKER_LABELS.get(k, k)} for k in blocker_keys
        ],
        "checks": {
            "ssl_ok": audit.ssl_ok,
            "impressum_ok": audit.impressum_ok,
            "datenschutz_ok": audit.datenschutz_ok,
            "lcp_value": audit.lcp_value,
            "cls_value": audit.cls_value,
            "inp_value": audit.inp_value,
            "mobile_score": audit.mobile_score,
            "performance_score": audit.performance_score,
        },
        "ai_summary": audit.ai_summary,
        "top_issues": _json_field(audit.top_issues, []),
        "recommendations": _json_field(audit.recommendations, []),
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "screenshot_url": f"data:image/jpeg;base64,{audit.screenshot_base64}" if getattr(audit, 'screenshot_base64', None) else None,
    }
