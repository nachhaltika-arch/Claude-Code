"""
PageSpeed-Insights-Erhebung für das Website-Audit.

Liefert Performance-Kennzahlen UND die Lighthouse-Barrierefreiheits-Audits.
Der Altcode forderte 'category=accessibility' zwar an, warf das Ergebnis aber weg
und vergab stattdessen feste Punkte — jede Website bekam 10 von 20.

Ist kein API-Key gesetzt oder scheitert der Aufruf, wird das als
``collected: False`` zurückgegeben. Es werden keine Werte mehr erfunden.
"""
import logging
import os
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Der korrekte Endpunkt ist 'runPagespeed'. Der Altcode rief 'runPagespeedTest'
# auf — den es nicht gibt. Mit gesetztem Key lief damit jeder Aufruf ins Leere.
PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

PSI_TIMEOUT = 30.0

# Lighthouse-Audits je Barrierefreiheits-Kriterium.
A11Y_AUDIT_GROUPS = {
    "kontrast": ("color-contrast",),
    "tastatur": ("bypass", "tabindex", "accesskeys", "meta-refresh"),
    "screenreader": (
        "image-alt", "label", "link-name", "button-name",
        "html-has-lang", "document-title", "aria-required-attr",
        "aria-valid-attr-value",
    ),
    "lesbarkeit": ("font-size", "meta-viewport", "heading-order"),
}


def api_key() -> str:
    return os.getenv("GOOGLE_PAGESPEED_API_KEY", "").strip()


async def fetch_pagespeed(url: str, strategy: str = "mobile") -> dict:
    """Ruft PageSpeed Insights ab und extrahiert Kennzahlen plus A11y-Audits.

    Ohne API-Key läuft der Aufruf trotzdem — PageSpeed v5 erlaubt anonyme
    Anfragen, nur mit deutlich kleinerem Kontingent. Erst wenn auch das
    scheitert, gilt die Kategorie als nicht erhoben.
    """
    key = api_key()
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility"],
    }
    if key:
        params["key"] = key

    try:
        async with httpx.AsyncClient(timeout=PSI_TIMEOUT) as client:
            r = await client.get(PSI_ENDPOINT, params=params)

        if r.status_code == 429:
            return {
                "collected": False,
                "strategy": strategy,
                "reason": "kontingent_erschoepft" if key else "kontingent_ohne_api_key",
                "detail": (
                    "PageSpeed-Kontingent erschöpft"
                    if key else
                    "Anonymes PageSpeed-Kontingent erschöpft — "
                    "GOOGLE_PAGESPEED_API_KEY setzen"
                ),
            }

        if r.status_code != 200:
            return {
                "collected": False,
                "strategy": strategy,
                "reason": "api_fehler",
                "detail": f"HTTP {r.status_code}: {r.text[:200]}",
            }

        result = _parse(r.json(), strategy)
        result["used_api_key"] = bool(key)
        return result

    except Exception as e:  # noqa: BLE001 — Erhebung darf das Audit nie abbrechen
        logger.warning(f"PageSpeed fehlgeschlagen für {url} ({strategy}): {e}")
        return {
            "collected": False,
            "strategy": strategy,
            "reason": "ausnahme",
            "detail": f"{type(e).__name__}: {e}"[:200],
        }


def _parse(data: dict, strategy: str) -> dict:
    lhr = data.get("lighthouseResult", {}) or {}
    categories = lhr.get("categories", {}) or {}
    audits = lhr.get("audits", {}) or {}

    performance = _category_score(categories, "performance")
    accessibility = _category_score(categories, "accessibility")

    lcp = _numeric(audits, "largest-contentful-paint")
    cls = _numeric(audits, "cumulative-layout-shift")
    tbt = _numeric(audits, "total-blocking-time")

    inp, inp_source = _field_inp(data)

    return {
        "collected": True,
        "strategy": strategy,
        "performance_score": performance,
        "accessibility_score": accessibility,
        "lcp_seconds": round(lcp / 1000, 2) if lcp is not None else None,
        "cls_value": round(cls, 3) if cls is not None else None,
        "tbt_ms": round(tbt) if tbt is not None else None,
        "inp_ms": inp,
        "inp_source": inp_source,
        "a11y_audits": _a11y_scores(audits),
        "a11y_failures": _a11y_failures(audits),
    }


def _category_score(categories: dict, name: str) -> Optional[int]:
    raw = (categories.get(name) or {}).get("score")
    return round(raw * 100) if isinstance(raw, (int, float)) else None


def _numeric(audits: dict, key: str) -> Optional[float]:
    value = (audits.get(key) or {}).get("numericValue")
    return value if isinstance(value, (int, float)) else None


def _field_inp(data: dict) -> tuple:
    """INP kommt ausschließlich aus CrUX-Felddaten.

    Lighthouse misst im Labor kein INP. Der Altcode las den Wert dennoch aus den
    Lab-Audits, bekam nie einen Treffer und schrieb den Platzhalter 999 ms in den
    Report — der dann als gemessene Interaktionszeit angezeigt wurde.
    """
    for block in ("loadingExperience", "originLoadingExperience"):
        metrics = (data.get(block) or {}).get("metrics") or {}
        entry = metrics.get("INTERACTION_TO_NEXT_PAINT")
        if entry and isinstance(entry.get("percentile"), (int, float)):
            scope = "seite" if block == "loadingExperience" else "domain"
            return entry["percentile"], f"crux_{scope}"
    return None, None


def _a11y_scores(audits: dict) -> Dict[str, Optional[float]]:
    """Mittelwert je Kriteriengruppe — None, wenn Lighthouse nichts geliefert hat."""
    result: Dict[str, Optional[float]] = {}
    for group, audit_ids in A11Y_AUDIT_GROUPS.items():
        scores = [
            audits[a]["score"]
            for a in audit_ids
            if a in audits and isinstance(audits[a].get("score"), (int, float))
        ]
        result[group] = round(sum(scores) / len(scores), 3) if scores else None
    return result


def _a11y_failures(audits: dict) -> list:
    """Konkret durchgefallene Barrierefreiheits-Prüfungen für den Report."""
    failures = []
    for group_audits in A11Y_AUDIT_GROUPS.values():
        for audit_id in group_audits:
            audit = audits.get(audit_id)
            if audit and audit.get("score") == 0:
                failures.append({
                    "id": audit_id,
                    "title": audit.get("title", audit_id),
                })
    return failures
