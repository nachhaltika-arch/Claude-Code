"""
Faktenerhebung für das Website-Audit.

Lädt die Startseite einmal und leitet daraus alle DOM-basierten Prüfungen ab.
Netzwerkabhängige Erhebungen laufen parallel; jede darf einzeln scheitern, ohne
das Audit zu stoppen — das betroffene Kriterium wird dann als 'nicht erhoben'
geführt.

Bindet die bereits vorhandenen Dienste ein, die im Altcode ungenutzt herumlagen:
qa_scanner (~45 echte Checks), hosting_scraper und link_checker.
"""
import asyncio
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from services import audit_collectors as collectors
from services.audit_pagespeed import fetch_pagespeed
from services.url_guard import UnsafeUrlError, fetch_guarded

logger = logging.getLogger(__name__)

HOMEPAGE_TIMEOUT = 15.0
COLLECTION_TIMEOUT = 200.0  # Faktenerhebung; die KI-Bewertung läuft danach

# Verbindungsversuche für die Startseite. Ein einzelner Fehlversuch beendet
# sonst das ganze Audit — der Besucher liest „Audit fehlgeschlagen“, obwohl
# seine Seite in Ordnung ist.
HOMEPAGE_ATTEMPTS = 3
HOMEPAGE_RETRY_DELAY = 1.5

USER_AGENT = collectors.USER_AGENT

SHOP_LEGAL_MARKERS = {
    "agb": ("agb", "allgemeine geschäftsbedingungen"),
    "widerruf": ("widerruf", "widerrufsbelehrung", "widerrufsrecht"),
    "versand": ("versandkosten", "lieferzeit", "versand und"),
}


async def fetch_homepage(url: str) -> dict:
    """Lädt die Startseite mit aktiver Zertifikatsprüfung.

    Der Altcode nutzte ``verify=False`` — damit blieben ungültige Zertifikate
    unsichtbar und wurden trotzdem mit der vollen SSL-Punktzahl belohnt. Die
    Prüfung bleibt deshalb an.

    Ein Verbindungsfehler wird jedoch wiederholt: beobachtet wurde, dass
    dieselbe Adresse mal einwandfrei antwortet und mal ein selbstsigniertes
    Zertifikat liefert — Server, deren Vhost nur für einen Teil ihrer
    IP-Adressen (v4/v6) ein passendes Zertifikat führt, verhalten sich je
    nach gewählter Adresse unterschiedlich. Ein einzelner Fehlversuch darf
    das Audit nicht beenden.
    """
    letzter_fehler = None

    for versuch in range(HOMEPAGE_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=HOMEPAGE_TIMEOUT, verify=True) as client:
                # Jede Weiterleitung einzeln geprüft — sonst wäre nur der erste
                # Hop kontrolliert und ein Redirect ins interne Netz käme durch.
                r = await fetch_guarded(client, url, headers={"User-Agent": USER_AGENT})
            return {
                "collected": True,
                "reachable": r.status_code < 400,
                "status_code": r.status_code,
                "html": r.text,
                "headers": dict(r.headers),
                "final_url": str(r.url),
            }
        except UnsafeUrlError as e:
            # Kein Netzproblem, sondern eine bewusst abgelehnte Adresse —
            # ein weiterer Versuch änderte daran nichts.
            return {"collected": True, "reachable": False, "status_code": 0,
                    "html": "", "headers": {}, "error": f"Adresse nicht erlaubt: {e}"[:200]}
        except httpx.ConnectError as e:
            letzter_fehler = f"Verbindung fehlgeschlagen: {e}"
        except Exception as e:  # noqa: BLE001
            letzter_fehler = f"{type(e).__name__}: {e}"

        if versuch + 1 < HOMEPAGE_ATTEMPTS:
            logger.warning(
                f"Startseite {url}: Versuch {versuch + 1} von {HOMEPAGE_ATTEMPTS} "
                f"fehlgeschlagen ({letzter_fehler}) — neuer Versuch")
            await asyncio.sleep(HOMEPAGE_RETRY_DELAY)

    logger.warning(f"Startseite {url} nach {HOMEPAGE_ATTEMPTS} Versuchen nicht erreichbar: "
                   f"{letzter_fehler}")
    return {"collected": True, "reachable": False, "status_code": 0,
            "html": "", "headers": {}, "error": (letzter_fehler or "unbekannt")[:200]}


def _security_headers(headers: dict) -> dict:
    lower = {k.lower(): v for k, v in headers.items()}
    return {
        "collected": True,
        "hsts": "strict-transport-security" in lower,
        "csp": "content-security-policy" in lower,
        "xframe": "x-frame-options" in lower,
        "xcontent": "x-content-type-options" in lower,
    }


def _shop_legal_markers(html: str) -> dict:
    lower = html.lower()
    return {name: any(k in lower for k in keys) for name, keys in SHOP_LEGAL_MARKERS.items()}


async def _safe(coro, label: str):
    """Führt eine Erhebung aus und schluckt nur deren eigenen Fehler."""
    try:
        return await coro
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Erhebung '{label}' fehlgeschlagen: {type(e).__name__}: {e}")
        return {"collected": False, "reason": f"{type(e).__name__}: {e}"[:200]}


async def _run_qa_scanner(url: str, company: str, trade: str) -> dict:
    from services.qa_scanner import run_full_qa

    scan = await run_full_qa(url, company, trade)
    return scan.get("checks", {}) or {}


async def _run_hosting(url: str) -> dict:
    from services.hosting_scraper import scrape_hosting_info

    return await scrape_hosting_info(url)


async def _run_link_check(url: str) -> dict:
    from services.link_checker import LinkChecker

    return await asyncio.to_thread(LinkChecker.check_links, url)


async def collect_facts(
    url: str,
    company_name: str = "",
    trade: str = "",
    city: str = "",
    current_year: int = 2026,
) -> dict:
    """Erhebt alle Fakten zu einer Website. Wirft nie — meldet Teilausfälle."""
    homepage = await fetch_homepage(url)

    if not homepage.get("reachable"):
        return {
            "url": url,
            "reachable": False,
            "status_code": homepage.get("status_code", 0),
            "error": homepage.get("error", ""),
        }

    html = homepage["html"]
    soup = BeautifulSoup(html, "html.parser")
    base_url = homepage.get("final_url") or url

    # Netzwerkabhängige Erhebungen parallel
    tasks = {
        "psi_mobile": _safe(fetch_pagespeed(base_url, "mobile"), "pagespeed"),
        "qa": _safe(_run_qa_scanner(base_url, company_name, trade), "qa_scanner"),
        "hosting": _safe(_run_hosting(base_url), "hosting_scraper"),
        "links": _safe(_run_link_check(base_url), "link_checker"),
        "legal": _safe(collectors.check_legal_pages(base_url, soup), "rechtsseiten"),
        "images": _safe(collectors.analyse_images(soup, base_url), "bilder"),
        "redirect": _safe(collectors.check_https_redirect(base_url), "https_redirect"),
        "tls": _safe(asyncio.to_thread(collectors.check_tls, base_url), "tls"),
    }

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks.values(), return_exceptions=True),
            timeout=COLLECTION_TIMEOUT,
        )
        collected = dict(zip(tasks.keys(), results))
    except asyncio.TimeoutError:
        logger.warning(f"Faktenerhebung für {url}: Gesamt-Timeout erreicht")
        collected = {}

    facts = {
        "url": url,
        "final_url": base_url,
        "city": city,
        "company_name": company_name,
        "trade": trade,
        "reachable": True,
        "status_code": homepage.get("status_code"),
        # DOM-basiert — kein zusätzlicher Netzwerkaufruf nötig
        "consent": collectors.detect_consent(html),
        "third_parties": collectors.detect_third_parties(html),
        "forms": collectors.analyse_forms(soup, base_url),
        "navigation": collectors.analyse_navigation(soup),
        "contact": collectors.analyse_contact(soup),
        "cta": collectors.analyse_cta(soup),
        "trust": collectors.analyse_trust(soup),
        "services": collectors.analyse_service_pages(soup, base_url),
        "freshness": collectors.analyse_freshness(html, current_year),
        "shop": collectors.detect_shop(html),
        "shop_legal_markers": _shop_legal_markers(html),
        "cdn": collectors.detect_cdn(homepage.get("headers", {})),
        "security_headers": _security_headers(homepage.get("headers", {})),
        "word_count": len(soup.get_text(" ").split()),
        "page_text": soup.get_text(" ", strip=True)[:6000],
    }

    for key, value in collected.items():
        facts[key] = value if isinstance(value, dict) else {"collected": False}

    return facts


def summarise_facts(facts: dict) -> dict:
    """Verdichtet die Rohfakten auf das, was Report und KI-Prompt brauchen."""
    psi = facts.get("psi_mobile") or {}
    tls = facts.get("tls") or {}
    qa = facts.get("qa") or {}
    legal = facts.get("legal") or {}
    links = facts.get("links") or {}
    hosting = facts.get("hosting") or {}

    return {
        "lcp_value": psi.get("lcp_seconds"),
        "cls_value": psi.get("cls_value"),
        "inp_value": psi.get("inp_ms"),
        "inp_source": psi.get("inp_source"),
        "performance_score": psi.get("performance_score"),
        "mobile_score": psi.get("performance_score"),
        "accessibility_score": psi.get("accessibility_score"),
        "pagespeed_collected": bool(psi.get("collected")),
        "pagespeed_reason": psi.get("reason"),
        "ssl_ok": bool(tls.get("valid")),
        "ssl_detail": tls.get("reason") or tls.get("issuer") or "",
        "impressum_ok": bool(legal.get("impressum", {}).get("reachable")),
        "impressum_complete": bool(legal.get("impressum", {}).get("complete")),
        "datenschutz_ok": bool(legal.get("datenschutz", {}).get("reachable")),
        "datenschutz_complete": bool(legal.get("datenschutz", {}).get("complete")),
        "broken_links": len(links.get("broken_links", []) or []),
        "hosting_provider": hosting.get("hosting_provider"),
        "detected_technologies": hosting.get("detected_technologies", []),
        "a11y_failures": [f["title"] for f in (psi.get("a11y_failures") or [])][:8],
        # GEO-Prüfpunkte. Sie standen im Bericht, ohne je erhoben zu werden —
        # die Spalten blieben leer, das PDF las die Leere als „nicht erfüllt"
        # und druckte Handlungsaufforderungen. `None` heißt hier unbekannt und
        # ist nicht dasselbe wie `False` („gemessen und nicht vorhanden").
        "llms_txt": qa.get("llms_txt") if qa else None,
        "robots_ai_friendly": qa.get("robots_ai_friendly") if qa else None,
        "structured_data": qa.get("schema_markup") if qa else None,
        "gesperrte_ki_crawler": (qa.get("gesperrte_ki_crawler") or []) if qa else [],
    }


def collection_notes(facts: dict, ai: Optional[dict] = None) -> dict:
    """Warum eine Prüfung ausfiel — damit 'nicht erhoben' begründet erscheint.

    Ohne diese Notiz sieht der Betrachter nur fehlende Punkte und kann nicht
    unterscheiden, ob die Website ein Problem hat oder das Audit eines.
    """
    notes = {}
    for key, label in (
        ("psi_mobile", "pagespeed"),
        ("legal", "rechtsseiten"),
        ("tls", "tls"),
        ("links", "linkpruefung"),
        ("hosting", "hosting"),
    ):
        fact = facts.get(key) or {}
        if fact.get("collected") is False:
            notes[label] = {
                "reason": fact.get("reason", "unbekannt"),
                "detail": str(fact.get("detail", ""))[:200],
            }

    # Steht hinter der Seite kein Betrieb, fallen die angebotsbezogenen
    # Kriterien heraus (siehe audit_scoring._apply_ai). Ohne diese Notiz sieht
    # der Leser nur eine niedrigere Abdeckung und erfährt nicht, warum.
    if ai and ai.get("betriebsseite") is False:
        notes["angebotskriterien"] = {
            "reason": "keine_betriebsseite",
            "detail": str(ai.get("branche") or "")[:200],
        }

    return notes
