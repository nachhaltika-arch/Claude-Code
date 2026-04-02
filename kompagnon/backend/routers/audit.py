"""
Website Audit API routes.
POST /api/audit/start - Run full website audit
GET  /api/audit/{audit_id} - Get audit result
GET  /api/audit/lead/{lead_id} - All audits for a lead
"""
import json
import os
import re
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import AuditResult, Lead, get_db

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])

PAGESPEED_API_KEY = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

LEVELS = [
    (95, "Homepage Standard Platin"),
    (85, "Homepage Standard Gold"),
    (70, "Homepage Standard Silber"),
    (50, "Homepage Standard Bronze"),
    (0, "Nicht konform"),
]


# ═══════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════

class AuditRequest(BaseModel):
    website_url: str
    company_name: str = ""
    contact_name: str = ""
    city: str = ""
    trade: str = ""
    lead_id: Optional[int] = None


class LinkLeadRequest(BaseModel):
    lead_id: int


# ═══════════════════════════════════════════════════════════
# Technical Checks
# ═══════════════════════════════════════════════════════════

def _normalise_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _check_ssl(url: str) -> bool:
    return url.startswith("https://")


def _check_reachable(url: str) -> dict:
    try:
        r = requests.get(url, timeout=4, allow_redirects=True)
        return {"reachable": r.status_code == 200, "status_code": r.status_code, "html": r.text}
    except Exception as e:
        return {"reachable": False, "status_code": 0, "html": "", "error": str(e)}


def _check_legal_pages(html: str, url: str) -> dict:
    html_lower = html.lower()
    links = re.findall(r'href=["\']([^"\']*)["\']', html_lower)
    all_text = html_lower + " ".join(links)

    impressum = any(
        kw in all_text
        for kw in ["impressum", "/impressum", "imprint"]
    )
    datenschutz = any(
        kw in all_text
        for kw in ["datenschutz", "privacy", "/datenschutz", "datenschutzerkl"]
    )
    cookie_banner = any(
        kw in all_text
        for kw in [
            "cookie", "consent", "cookiebot", "cookieconsent",
            "onetrust", "usercentrics", "borlabs", "gdpr",
        ]
    )
    return {
        "impressum_ok": impressum,
        "datenschutz_ok": datenschutz,
        "cookie_banner": cookie_banner,
    }


def _check_pagespeed(url: str) -> dict:
    """Call Google PageSpeed Insights API."""
    defaults = {
        "performance_score": 0,
        "mobile_score": 0,
        "lcp_value": 99.0,
        "cls_value": 1.0,
        "inp_value": 999.0,
    }
    if not PAGESPEED_API_KEY:
        # Simulate reasonable values when no API key
        return {
            "performance_score": 55,
            "mobile_score": 50,
            "lcp_value": 3.8,
            "cls_value": 0.18,
            "inp_value": 320.0,
        }

    try:
        api_url = (
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeedTest"
            f"?url={url}&key={PAGESPEED_API_KEY}&strategy=mobile"
            "&category=performance&category=accessibility"
        )
        r = requests.get(api_url, timeout=10)
        if r.status_code != 200:
            return defaults
        data = r.json()

        lhr = data.get("lighthouseResult", {})
        categories = lhr.get("categories", {})
        audits = lhr.get("audits", {})

        perf = categories.get("performance", {}).get("score", 0)
        perf = int((perf or 0) * 100)

        lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 99000) / 1000
        cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 1.0)
        inp_audit = audits.get("interaction-to-next-paint", {})
        inp_val = inp_audit.get("numericValue", 999.0) if inp_audit else 999.0

        return {
            "performance_score": perf,
            "mobile_score": perf,
            "lcp_value": round(lcp, 2),
            "cls_value": round(cls, 3),
            "inp_value": round(inp_val, 0),
        }
    except Exception as e:
        logger.error(f"PageSpeed API error: {e}")
        return defaults


def _check_security_headers(url: str) -> dict:
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        headers = {k.lower(): v for k, v in r.headers.items()}
        return {
            "has_hsts": "strict-transport-security" in headers,
            "has_csp": "content-security-policy" in headers,
            "has_xframe": "x-frame-options" in headers,
            "has_xcontent": "x-content-type-options" in headers,
        }
    except Exception:
        return {"has_hsts": False, "has_csp": False, "has_xframe": False, "has_xcontent": False}


# ═══════════════════════════════════════════════════════════
# AI Scoring via Claude
# ═══════════════════════════════════════════════════════════

def _ai_score(check_data: dict, company_name: str, trade: str) -> dict:
    """Use Claude to analyze checks and assign granular item-level scores."""

    scoring_prompt = """Du bist ein Website-Auditor für den "Homepage Standard" Bewertungsrahmen.
Analysiere die technischen Prüfergebnisse und vergib Punkte für alle Einzelkriterien.

BEWERTUNGSSCHEMA — Einzelkriterien (Gesamt: 100 Punkte):

RECHTLICHE COMPLIANCE (Summe max 30):
- rc_impressum: Impressum vorhanden (0-7)
- rc_datenschutz: Datenschutzerklärung (0-7)
- rc_cookie: Cookie Consent (TDDDG) (0-6)
- rc_bfsg: Barrierefreiheitserklärung (BFSG) (0-4)
- rc_urheberrecht: Urheberrecht & Lizenzen (0-3)
- rc_ecommerce: E-Commerce Pflichten (0-3)

TECHNISCHE PERFORMANCE (Summe max 20):
- tp_lcp: LCP < 2.5s = 5P, < 4s = 2P, sonst 0 (0-5)
- tp_cls: CLS < 0.1 = 4P, < 0.25 = 2P, sonst 0 (0-4)
- tp_inp: INP < 200ms = 3P, < 500ms = 1P, sonst 0 (0-3)
- tp_mobile: Mobile-First Bewertung (0-4)
- tp_bilder: Bildoptimierung (0-4)

HOSTING & INFRASTRUKTUR (nicht im Score, je 0 oder 1):
- ho_anbieter: Hosting-Anbieter identifizierbar (0-1)
- ho_uptime: Website erreichbar/zuverlässig (0-1)
- ho_http: HTTP leitet auf HTTPS weiter (0-1)
- ho_backup: Backup-Hinweise erkennbar (0-1)
- ho_cdn: CDN wird genutzt (0-1)

BARRIEREFREIHEIT (Summe max 20):
- bf_kontrast: Farbkontraste WCAG AA (0-5)
- bf_tastatur: Tastaturzugänglichkeit (0-5)
- bf_screenreader: Screenreader-Kompatibilität (0-5)
- bf_lesbarkeit: Lesbarkeit & Textgröße (0-5)

SICHERHEIT & DATENSCHUTZ (Summe max 15):
- si_ssl: HTTPS/SSL (0-4)
- si_header: Security-Header HSTS/CSP/X-Frame (0-4)
- si_drittanbieter: DSGVO Drittanbieter (0-4)
- si_formulare: Formularsicherheit (0-3)

SEO & SICHTBARKEIT (Summe max 10):
- se_seo: Technische SEO Grundlagen (0-4)
- se_schema: Strukturierte Daten Schema.org (0-3)
- se_lokal: Lokale Auffindbarkeit (0-3)

INHALT & NUTZERERFAHRUNG (Summe max 5, ux_kontakt zählt extra):
- ux_erstindruck: Erster Eindruck (0-1)
- ux_cta: Klare Call-to-Action (0-1)
- ux_navigation: Navigation & Struktur (0-1)
- ux_vertrauen: Vertrauenssignale (0-1)
- ux_content: Content-Qualität (0-1)
- ux_kontakt: Kontaktmöglichkeiten (0-1)

REGELN:
- Antworte NUR als valides JSON, KEIN Markdown
- Sei streng aber fair — vergib nur Punkte wenn es Belege gibt
- Für nicht direkt prüfbare Kriterien: konservative Schätzung
- ai_summary: 3-5 Sätze in einfacher Sprache für den Betriebsinhaber
- top_issues: Die 3 größten konkreten Probleme
- recommendations: 3-5 konkrete nächste Schritte"""

    user_message = f"""Analysiere diese Website-Prüfungsdaten:

Betrieb: {company_name}
Gewerk: {trade}

Technische Prüfungsergebnisse:
{json.dumps(check_data, indent=2, ensure_ascii=False)}

Antworte als JSON mit allen Einzelkriterienpunkten:
{{
  "rc_impressum": 0, "rc_datenschutz": 0, "rc_cookie": 0, "rc_bfsg": 0, "rc_urheberrecht": 0, "rc_ecommerce": 0,
  "tp_lcp": 0, "tp_cls": 0, "tp_inp": 0, "tp_mobile": 0, "tp_bilder": 0,
  "ho_anbieter": 0, "ho_uptime": 0, "ho_http": 0, "ho_backup": 0, "ho_cdn": 0,
  "bf_kontrast": 0, "bf_tastatur": 0, "bf_screenreader": 0, "bf_lesbarkeit": 0,
  "si_ssl": 0, "si_header": 0, "si_drittanbieter": 0, "si_formulare": 0,
  "se_seo": 0, "se_schema": 0, "se_lokal": 0,
  "ux_erstindruck": 0, "ux_cta": 0, "ux_navigation": 0, "ux_vertrauen": 0, "ux_content": 0, "ux_kontakt": 0,
  "ai_summary": "...",
  "top_issues": ["Problem 1", "Problem 2", "Problem 3"],
  "recommendations": ["Empfehlung 1", "Empfehlung 2", "Empfehlung 3"]
}}"""

    if not ANTHROPIC_API_KEY:
        return _mock_ai_score(check_data)

    def extract_json(text: str):
        """Robustly extract a JSON object from an LLM response."""
        import re as _re
        # 1. Direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
        # 2. Find first {...} block
        match = _re.search(r'\{.*\}', text, _re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        # 3. Repair: append missing closing brace
        try:
            repaired = text.strip()
            if not repaired.endswith('}'):
                repaired += '}'
            return json.loads(repaired)
        except Exception:
            return None

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=0, timeout=25.0)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=scoring_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        if not raw:
            logger.warning('AI scoring: Leere Antwort')
            return _mock_ai_score(check_data)
        result = extract_json(raw)
        if result is None:
            logger.warning(f'AI scoring: JSON nicht parsebar, verwende Fallback. Rohantwort: {raw[:300]}')
            return _mock_ai_score(check_data)
        return result
    except Exception as e:
        logger.error(f"AI scoring failed: {e}")
        return _mock_ai_score(check_data)


def _mock_ai_score(check_data: dict) -> dict:
    """Deterministic fallback scoring returning all item-level scores."""
    lcp = check_data.get("lcp_value", 99)
    cls_v = check_data.get("cls_value", 1)
    inp = check_data.get("inp_value", 999)
    mobile = check_data.get("mobile_score", 0)
    sec = check_data.get("security_headers", {})

    # RC items
    rc_impressum = 7 if check_data.get("impressum_ok") else 0
    rc_datenschutz = 7 if check_data.get("datenschutz_ok") else 0
    rc_cookie = 6 if check_data.get("cookie_banner") else 0
    rc_bfsg = 0
    rc_urheberrecht = 2
    rc_ecommerce = 2

    # TP items
    tp_lcp = 5 if lcp < 2.5 else (2 if lcp < 4.0 else 0)
    tp_cls = 4 if cls_v < 0.1 else (2 if cls_v < 0.25 else 0)
    tp_inp = 3 if inp < 200 else (1 if inp < 500 else 0)
    tp_mobile = 4 if mobile >= 80 else (2 if mobile >= 50 else 0)
    tp_bilder = 1

    # HO items (hosting checks)
    ho_anbieter = 1
    ho_uptime = 1 if check_data.get("reachable") else 0
    ho_http = 1 if check_data.get("ssl_ok") else 0
    ho_backup = 0
    ho_cdn = 0

    # BF items — conservative without deep scan
    bf_kontrast = 3
    bf_tastatur = 2
    bf_screenreader = 2
    bf_lesbarkeit = 3

    # SI items
    si_ssl = 4 if check_data.get("ssl_ok") else 0
    si_header = min(sum(1 for v in sec.values() if v), 4)
    si_drittanbieter = 2
    si_formulare = 1

    # SE items — conservative without deep crawl
    se_seo = 2
    se_schema = 0
    se_lokal = 1

    # UX items — conservative
    ux_erstindruck = 1
    ux_cta = 1
    ux_navigation = 1
    ux_vertrauen = 0
    ux_content = 1
    ux_kontakt = 1

    total = (rc_impressum + rc_datenschutz + rc_cookie + rc_bfsg + rc_urheberrecht + rc_ecommerce
             + tp_lcp + tp_cls + tp_inp + tp_mobile + tp_bilder
             + bf_kontrast + bf_tastatur + bf_screenreader + bf_lesbarkeit
             + si_ssl + si_header + si_drittanbieter + si_formulare
             + se_seo + se_schema + se_lokal
             + min(ux_erstindruck + ux_cta + ux_navigation + ux_vertrauen + ux_content + ux_kontakt, 5))

    issues = []
    if not check_data.get("impressum_ok"):
        issues.append("Kein Impressum gefunden — gesetzliche Pflicht nach TMG/DDG")
    if not check_data.get("datenschutz_ok"):
        issues.append("Keine Datenschutzerklärung — DSGVO-Verstoß")
    if lcp >= 2.5:
        issues.append(f"Ladezeit zu hoch (LCP: {lcp:.1f}s) — Nutzer springen ab")
    if not check_data.get("ssl_ok"):
        issues.append("Kein HTTPS — Browser zeigen Warnung, Google straft ab")
    if not check_data.get("cookie_banner"):
        issues.append("Kein Cookie-Banner erkennbar — DSGVO-Risiko")

    recs = [
        "Impressum und Datenschutzerklärung prüfen und aktualisieren",
        "Website-Performance optimieren (Bilder komprimieren, Caching aktivieren)",
        "Cookie-Consent-Lösung implementieren (z.B. Borlabs, Usercentrics)",
        "Security-Header konfigurieren (HSTS, CSP, X-Frame-Options)",
        "Mobile-Optimierung verbessern für bessere Google-Rankings",
    ]

    return {
        "rc_impressum": rc_impressum, "rc_datenschutz": rc_datenschutz,
        "rc_cookie": rc_cookie, "rc_bfsg": rc_bfsg,
        "rc_urheberrecht": rc_urheberrecht, "rc_ecommerce": rc_ecommerce,
        "tp_lcp": tp_lcp, "tp_cls": tp_cls, "tp_inp": tp_inp,
        "tp_mobile": tp_mobile, "tp_bilder": tp_bilder,
        "ho_anbieter": ho_anbieter, "ho_uptime": ho_uptime, "ho_http": ho_http,
        "ho_backup": ho_backup, "ho_cdn": ho_cdn,
        "bf_kontrast": bf_kontrast, "bf_tastatur": bf_tastatur,
        "bf_screenreader": bf_screenreader, "bf_lesbarkeit": bf_lesbarkeit,
        "si_ssl": si_ssl, "si_header": si_header,
        "si_drittanbieter": si_drittanbieter, "si_formulare": si_formulare,
        "se_seo": se_seo, "se_schema": se_schema, "se_lokal": se_lokal,
        "ux_erstindruck": ux_erstindruck, "ux_cta": ux_cta,
        "ux_navigation": ux_navigation, "ux_vertrauen": ux_vertrauen,
        "ux_content": ux_content, "ux_kontakt": ux_kontakt,
        "ai_summary": (
            f"Die Website von {check_data.get('company_name', 'Ihrem Betrieb')} "
            f"erreicht {'gute' if total >= 70 else 'ausbaufähige'} Werte im Homepage Standard Audit. "
            f"{'Die rechtlichen Grundlagen sind vorhanden.' if check_data.get('impressum_ok') and check_data.get('datenschutz_ok') else 'Es fehlen wichtige rechtliche Seiten wie Impressum oder Datenschutzerklärung.'} "
            f"Die technische Performance liegt {'im grünen Bereich' if mobile >= 70 else 'unter dem Optimum'}. "
            f"Mit gezielten Optimierungen kann die Sichtbarkeit bei Google deutlich gesteigert werden."
        ),
        "top_issues": issues[:3] if issues else ["Keine kritischen Probleme gefunden"],
        "recommendations": recs[:5],
    }


# ═══════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════

def _run_audit_background(audit_id: int):
    """Background worker — runs all checks and updates the DB record.
    Designed to complete within 25s for Render free-plan compatibility.
    """
    import time
    _start = time.monotonic()

    from database import SessionLocal
    db = SessionLocal()
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit:
            return

        audit.status = "running"
        db.commit()

        url = audit.website_url

        # 1. Basic checks
        ssl_ok = _check_ssl(url)
        site = _check_reachable(url)
        if not site["reachable"]:
            audit.status = "failed"
            audit.error_message = f"Website nicht erreichbar (Status {site.get('status_code', 'N/A')})"
            db.commit()
            return

        # 2. Legal checks
        legal = _check_legal_pages(site["html"], url)

        # 3+4. PageSpeed + Security headers IN PARALLEL (12s max)
        psi = {"performance_score": 0, "mobile_score": 0, "lcp_value": 99.0, "cls_value": 1.0, "inp_value": 999.0}
        sec = {"has_hsts": False, "has_csp": False, "has_xframe": False, "has_xcontent": False}
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_psi = pool.submit(_check_pagespeed, url)
                fut_sec = pool.submit(_check_security_headers, url)
                try:
                    sec = fut_sec.result(timeout=4)
                except Exception:
                    pass
                try:
                    psi = fut_psi.result(timeout=12)
                except Exception:
                    pass
        except Exception:
            pass

        # 5. Build check data bundle
        check_data = {
            "company_name": audit.company_name,
            "url": url,
            "ssl_ok": ssl_ok,
            "reachable": True,
            **legal,
            **psi,
            "security_headers": sec,
        }

        # 6. AI scoring (skip if already past 20s)
        elapsed = time.monotonic() - _start
        if elapsed < 20:
            ai = _ai_score(check_data, audit.company_name, audit.trade or "")
        else:
            logger.warning(f"Audit {audit_id}: skipping AI (elapsed {elapsed:.0f}s), using mock")
            ai = _mock_ai_score(check_data)

        # 7. Calculate category totals from item scores
        rc = min(sum(ai.get(k, 0) for k in [
            "rc_impressum", "rc_datenschutz", "rc_cookie", "rc_bfsg", "rc_urheberrecht", "rc_ecommerce"
        ]), 30)
        tp = min(sum(ai.get(k, 0) for k in [
            "tp_lcp", "tp_cls", "tp_inp", "tp_mobile", "tp_bilder"
        ]), 20)
        bf = min(sum(ai.get(k, 0) for k in [
            "bf_kontrast", "bf_tastatur", "bf_screenreader", "bf_lesbarkeit"
        ]), 20)
        si = min(sum(ai.get(k, 0) for k in [
            "si_ssl", "si_header", "si_drittanbieter", "si_formulare"
        ]), 15)
        se = min(sum(ai.get(k, 0) for k in [
            "se_seo", "se_schema", "se_lokal"
        ]), 10)
        ux = min(sum(ai.get(k, 0) for k in [
            "ux_erstindruck", "ux_cta", "ux_navigation", "ux_vertrauen", "ux_content", "ux_kontakt"
        ]), 5)
        total = rc + tp + bf + si + se + ux
        level = next(lbl for threshold, lbl in LEVELS if total >= threshold)

        # 8. Update category + aggregate fields
        audit.total_score = total
        audit.level = level
        audit.rc_score = rc
        audit.tp_score = tp
        audit.bf_score = bf
        audit.si_score = si
        audit.se_score = se
        audit.ux_score = ux
        audit.ssl_ok = ssl_ok
        audit.impressum_ok = legal["impressum_ok"]
        audit.datenschutz_ok = legal["datenschutz_ok"]
        audit.lcp_value = psi.get("lcp_value")
        audit.cls_value = psi.get("cls_value")
        audit.inp_value = psi.get("inp_value")
        audit.mobile_score = psi.get("mobile_score")
        audit.performance_score = psi.get("performance_score")
        audit.ai_summary = ai.get("ai_summary", "")
        audit.top_issues = json.dumps(ai.get("top_issues", []), ensure_ascii=False)
        audit.recommendations = json.dumps(ai.get("recommendations", []), ensure_ascii=False)

        # 8b. Save all item-level scores
        _ITEM_KEYS = [
            "rc_impressum", "rc_datenschutz", "rc_cookie", "rc_bfsg", "rc_urheberrecht", "rc_ecommerce",
            "tp_lcp", "tp_cls", "tp_inp", "tp_mobile", "tp_bilder",
            "ho_anbieter", "ho_uptime", "ho_http", "ho_backup", "ho_cdn",
            "bf_kontrast", "bf_tastatur", "bf_screenreader", "bf_lesbarkeit",
            "si_ssl", "si_header", "si_drittanbieter", "si_formulare",
            "se_seo", "se_schema", "se_lokal",
            "ux_erstindruck", "ux_cta", "ux_navigation", "ux_vertrauen", "ux_content", "ux_kontakt",
        ]
        for key in _ITEM_KEYS:
            setattr(audit, key, int(ai.get(key, 0) or 0))

        # 9. Screenshot (optional, non-blocking)
        try:
            import asyncio
            from services.screenshot import capture_screenshot
            screenshot_b64 = asyncio.run(capture_screenshot(url))
            if screenshot_b64:
                audit.screenshot_base64 = screenshot_b64
                if audit.lead_id:
                    from database import Lead as LeadModel
                    lead = db.query(LeadModel).filter(LeadModel.id == audit.lead_id).first()
                    if lead:
                        lead.website_screenshot = screenshot_b64
        except Exception as e:
            logger.warning(f"Screenshot skipped for audit {audit_id}: {e}")

        audit.status = "completed"
        db.commit()
        logger.info(f"✓ Audit {audit_id} completed: {total}/100 ({level})")

    except Exception as e:
        logger.error(f"✗ Audit {audit_id} failed: {e}")
        try:
            audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
            if audit:
                audit.status = "failed"
                audit.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.get("/recent")
def get_recent_audits(
    limit: int = 10,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    """Return the most recent completed audits, newest first."""
    audits = (
        db.query(AuditResult)
        .filter(AuditResult.status == "completed")
        .order_by(AuditResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "website_url": a.website_url,
            "company_name": a.company_name,
            "total_score": a.total_score,
            "level": a.level,
            "lead_id": a.lead_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in audits
    ]


@router.post("/start")
async def start_audit(
    req: AuditRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create audit record, auto-scrape website, and run checks in background."""
    url = _normalise_url(req.website_url)

    # Auto-scrape website for company info (fast, < 5s)
    scraped = {}
    try:
        from services.scraper import scrape_website
        scraped = await scrape_website(url)
    except Exception as e:
        logger.warning(f"Scraping failed for {url}: {e}")

    # Use scraped data as fallback when fields not provided
    company_name = req.company_name or scraped.get("company_name", "") or url
    city = req.city or scraped.get("city", "")
    trade = req.trade or scraped.get("trade", "Sonstiges")

    # Create pending record with scraped data
    audit = AuditResult(
        lead_id=req.lead_id,
        website_url=url,
        company_name=company_name,
        contact_name=req.contact_name,
        city=city,
        trade=trade,
        status="pending",
        scraped_phone=scraped.get("phone", ""),
        scraped_email=scraped.get("email", ""),
        scraped_description=scraped.get("meta_description", ""),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    # Kick off background processing
    background_tasks.add_task(_run_audit_background, audit.id)

    return {
        "id": audit.id,
        "status": "pending",
        "scraped": {
            "company_name": company_name,
            "city": city,
            "trade": trade,
            "phone": scraped.get("phone", ""),
            "email": scraped.get("email", ""),
        },
        "message": "Audit gestartet. Ergebnis mit GET /api/audit/{id} abrufen.",
    }


@router.get("/status/{audit_id}")
def get_audit_status(audit_id: int, db: Session = Depends(get_db)):
    """Poll audit status (pending / running / completed / failed)."""
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    result = {"id": audit.id, "status": audit.status}
    if audit.status == "failed":
        result["error"] = audit.error_message
    if audit.status == "completed":
        result["data"] = _format_audit(audit)
    return result


@router.get("/{audit_id}/pdf")
def download_audit_pdf(audit_id: int, db: Session = Depends(get_db)):
    """Download audit result as PDF report."""
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit:
            raise HTTPException(status_code=404, detail="Audit nicht gefunden")
        if audit.status != "completed":
            raise HTTPException(status_code=400, detail=f"Audit noch nicht abgeschlossen: {audit.status}")

        from services.pdf_generator import generate_audit_report
        pdf_bytes = generate_audit_report(audit.__dict__)

        safe_name = (audit.company_name or "Audit").replace(" ", "-").replace("/", "-")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="Homepage-Standard-Audit-{safe_name}-{audit.id}.pdf"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"PDF generation failed for audit {audit_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF-Generierung fehlgeschlagen: {str(e)}")


@router.get("/{audit_id}")
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    """Get a stored audit result."""
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit:
            raise HTTPException(status_code=404, detail="Audit nicht gefunden")
        if audit.status == "pending" or audit.status == "running":
            return {"id": audit.id, "status": audit.status, "message": "Audit läuft noch..."}
        if audit.status == "failed":
            return {"id": audit.id, "status": "failed", "message": audit.error_message or "Audit fehlgeschlagen",
                    "total_score": 0, "level": "", "website_url": audit.website_url or ""}
        return _format_audit(audit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Audit {audit_id} Fehler: {e}')
        raise HTTPException(status_code=500, detail=f'Audit konnte nicht geladen werden: {str(e)}')


@router.delete("/{audit_id}")
def delete_audit(audit_id: int, db: Session = Depends(get_db)):
    """Delete a single audit. Updates lead screenshot if needed."""
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    lead_id = audit.lead_id
    db.delete(audit)
    db.commit()
    # Update lead screenshot from remaining audits
    if lead_id:
        remaining = db.query(AuditResult).filter(
            AuditResult.lead_id == lead_id, AuditResult.status == "completed"
        ).order_by(AuditResult.created_at.desc()).first()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.website_screenshot = remaining.screenshot_base64 if remaining and getattr(remaining, 'screenshot_base64', None) else ""
            db.commit()
    return {"success": True, "message": "Audit geloescht"}


@router.patch("/{audit_id}/link-lead")
def link_audit_to_lead(audit_id: int, req: LinkLeadRequest, db: Session = Depends(get_db)):
    """Link an existing audit to a lead."""
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    audit.lead_id = req.lead_id
    db.commit()
    return {"id": audit.id, "lead_id": req.lead_id, "message": "Audit mit Lead verknüpft"}


@router.get("/lead/{lead_id}")
def get_audits_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get all audits for a specific lead."""
    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id)
        .order_by(AuditResult.created_at.desc())
        .all()
    )
    return [_format_audit(a) for a in audits]


_ITEM_KEYS = [
    "rc_impressum", "rc_datenschutz", "rc_cookie", "rc_bfsg", "rc_urheberrecht", "rc_ecommerce",
    "tp_lcp", "tp_cls", "tp_inp", "tp_mobile", "tp_bilder",
    "ho_anbieter", "ho_uptime", "ho_http", "ho_backup", "ho_cdn",
    "bf_kontrast", "bf_tastatur", "bf_screenreader", "bf_lesbarkeit",
    "si_ssl", "si_header", "si_drittanbieter", "si_formulare",
    "se_seo", "se_schema", "se_lokal",
    "ux_erstindruck", "ux_cta", "ux_navigation", "ux_vertrauen", "ux_content", "ux_kontakt",
]


def _format_audit(audit: AuditResult) -> dict:
    """Format audit for JSON response."""
    try:
        top_issues = json.loads(audit.top_issues) if audit.top_issues else []
    except (json.JSONDecodeError, TypeError):
        top_issues = []
    try:
        recommendations = json.loads(audit.recommendations) if audit.recommendations else []
    except (json.JSONDecodeError, TypeError):
        recommendations = []

    items = {k: int(getattr(audit, k, 0) or 0) for k in _ITEM_KEYS}

    return {
        "id": audit.id,
        "status": audit.status,
        "lead_id": audit.lead_id,
        "website_url": audit.website_url,
        "company_name": audit.company_name,
        "contact_name": audit.contact_name,
        "city": audit.city,
        "trade": audit.trade,
        "total_score": audit.total_score,
        "level": audit.level,
        "categories": {
            "rechtliche_compliance": {"score": audit.rc_score, "max": 30},
            "technische_performance": {"score": audit.tp_score, "max": 20},
            "barrierefreiheit": {"score": audit.bf_score, "max": 20},
            "sicherheit_datenschutz": {"score": audit.si_score, "max": 15},
            "seo_sichtbarkeit": {"score": audit.se_score, "max": 10},
            "inhalt_nutzererfahrung": {"score": audit.ux_score, "max": 5},
        },
        "items": items,
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
        "top_issues": top_issues,
        "recommendations": recommendations,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "screenshot_url": f"data:image/jpeg;base64,{audit.screenshot_base64}" if getattr(audit, 'screenshot_base64', None) else None,
    }
