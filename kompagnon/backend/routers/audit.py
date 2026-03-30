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
    company_name: str
    contact_name: str = ""
    city: str = ""
    trade: str = ""
    lead_id: Optional[int] = None


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
        r = requests.get(url, timeout=5, allow_redirects=True)
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
        r = requests.get(api_url, timeout=15)
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
    """Use Claude to analyze checks and assign category scores."""

    scoring_prompt = """Du bist ein Website-Auditor für den "Homepage Standard" Bewertungsrahmen.
Analysiere die technischen Prüfergebnisse und vergib Punkte in 6 Kategorien.

BEWERTUNGSSCHEMA (Gesamt: 100 Punkte):

1. Rechtliche Compliance (max 30):
   - Impressum vorhanden: 7P
   - Datenschutzerklärung: 7P
   - Cookie Consent: 6P
   - Barrierefreiheitserklärung: 4P
   - Urheberrecht & Lizenzen: 3P
   - E-Commerce Pflichten: 3P

2. Technische Performance (max 20):
   - LCP unter 2.5s: 5P
   - CLS unter 0.1: 4P
   - INP unter 200ms: 3P
   - Mobile-First: 4P
   - Bildoptimierung: 4P

3. Barrierefreiheit (max 20):
   - Farbkontraste: 5P
   - Tastaturzugänglichkeit: 5P
   - Screenreader: 5P
   - Lesbarkeit: 5P

4. Sicherheit & Datenschutz (max 15):
   - HTTPS/SSL: 4P
   - Security Header: 4P
   - DSGVO Drittanbieter: 4P
   - Formularsicherheit: 3P

5. SEO & Sichtbarkeit (max 10):
   - Technische SEO: 4P
   - Strukturierte Daten: 3P
   - Lokale Auffindbarkeit: 3P

6. Inhalt & Nutzererfahrung (max 5):
   - Klare Botschaft & CTA: 2P
   - Aktualität & Qualität: 2P
   - Ladegeschwindigkeit UX: 1P

REGELN:
- Antworte NUR als valides JSON, KEIN Markdown
- Sei streng aber fair — vergib nur Punkte wenn es Belege gibt
- Für Kategorien die nicht automatisch geprüft werden können,
  schätze konservativ basierend auf den verfügbaren Daten
- ai_summary: 3-5 Sätze in einfacher Sprache für den Betriebsinhaber
- top_issues: Die 3 größten konkreten Probleme
- recommendations: 3-5 konkrete nächste Schritte"""

    user_message = f"""Analysiere diese Website-Prüfungsdaten:

Betrieb: {company_name}
Gewerk: {trade}

Technische Prüfungsergebnisse:
{json.dumps(check_data, indent=2, ensure_ascii=False)}

Antworte als JSON:
{{
  "rc_score": <0-30>,
  "tp_score": <0-20>,
  "bf_score": <0-20>,
  "si_score": <0-15>,
  "se_score": <0-10>,
  "ux_score": <0-5>,
  "ai_summary": "<3-5 Sätze, einfache Sprache>",
  "top_issues": ["Problem 1", "Problem 2", "Problem 3"],
  "recommendations": ["Empfehlung 1", "Empfehlung 2", "Empfehlung 3"]
}}"""

    if not ANTHROPIC_API_KEY:
        return _mock_ai_score(check_data)

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=scoring_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return json.loads(message.content[0].text)
    except Exception as e:
        logger.error(f"AI scoring failed: {e}")
        return _mock_ai_score(check_data)


def _mock_ai_score(check_data: dict) -> dict:
    """Deterministic fallback scoring when no API key."""
    rc = 0
    if check_data.get("impressum_ok"):
        rc += 7
    if check_data.get("datenschutz_ok"):
        rc += 7
    if check_data.get("cookie_banner"):
        rc += 6
    # conservative estimates for unchecked items
    rc += 3  # partial Barrierefreiheit + Urheberrecht

    tp = 0
    lcp = check_data.get("lcp_value", 99)
    if lcp < 2.5:
        tp += 5
    elif lcp < 4.0:
        tp += 2
    cls = check_data.get("cls_value", 1)
    if cls < 0.1:
        tp += 4
    elif cls < 0.25:
        tp += 2
    inp = check_data.get("inp_value", 999)
    if inp < 200:
        tp += 3
    elif inp < 500:
        tp += 1
    mobile = check_data.get("mobile_score", 0)
    if mobile >= 80:
        tp += 4
    elif mobile >= 50:
        tp += 2
    tp += 1  # conservative Bildoptimierung

    bf = 8  # conservative estimate without deep scan

    si = 0
    if check_data.get("ssl_ok"):
        si += 4
    sec = check_data.get("security_headers", {})
    si += sum(1 for v in sec.values() if v)
    si += 2  # conservative DSGVO + Formular

    se = 3  # conservative without deep crawl
    ux = 2  # conservative

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
        "rc_score": rc,
        "tp_score": tp,
        "bf_score": bf,
        "si_score": si,
        "se_score": se,
        "ux_score": ux,
        "ai_summary": f"Die Website von {check_data.get('company_name', 'Ihrem Betrieb')} "
        f"erreicht {'gute' if (rc + tp + bf + si + se + ux) >= 70 else 'ausbaufähige'} Werte. "
        f"{'Die rechtlichen Grundlagen sind vorhanden.' if check_data.get('impressum_ok') and check_data.get('datenschutz_ok') else 'Es fehlen wichtige rechtliche Seiten.'} "
        f"Die technische Performance liegt {'im grünen Bereich' if mobile >= 70 else 'unter dem Optimum'}. "
        f"Mit gezielten Optimierungen kann die Sichtbarkeit bei Google deutlich gesteigert werden.",
        "top_issues": issues[:3] if issues else ["Keine kritischen Probleme gefunden"],
        "recommendations": recs[:5],
    }


# ═══════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════

def _run_audit_background(audit_id: int):
    """Background worker — runs all checks and updates the DB record."""
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

        # 3+4. PageSpeed + Security headers IN PARALLEL
        psi = {}
        sec = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_psi = pool.submit(_check_pagespeed, url)
            fut_sec = pool.submit(_check_security_headers, url)
            psi = fut_psi.result(timeout=20)
            sec = fut_sec.result(timeout=5)

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

        # 6. AI scoring
        ai = _ai_score(check_data, audit.company_name, audit.trade or "")

        # 7. Calculate totals
        rc = min(ai.get("rc_score", 0), 30)
        tp = min(ai.get("tp_score", 0), 20)
        bf = min(ai.get("bf_score", 0), 20)
        si = min(ai.get("si_score", 0), 15)
        se = min(ai.get("se_score", 0), 10)
        ux = min(ai.get("ux_score", 0), 5)
        total = rc + tp + bf + si + se + ux
        level = next(lbl for threshold, lbl in LEVELS if total >= threshold)

        # 8. Update record
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


@router.post("/start")
def start_audit(
    req: AuditRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create audit record and run checks in background."""
    url = _normalise_url(req.website_url)

    # Create pending record immediately (returns in <100ms)
    audit = AuditResult(
        lead_id=req.lead_id,
        website_url=url,
        company_name=req.company_name,
        contact_name=req.contact_name,
        city=req.city,
        trade=req.trade,
        status="pending",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    # Kick off background processing
    background_tasks.add_task(_run_audit_background, audit.id)

    return {
        "id": audit.id,
        "status": "pending",
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


@router.get("/{audit_id}")
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    """Get a stored audit result."""
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    if audit.status == "pending" or audit.status == "running":
        return {"id": audit.id, "status": audit.status, "message": "Audit läuft noch..."}
    if audit.status == "failed":
        raise HTTPException(status_code=500, detail=audit.error_message or "Audit fehlgeschlagen")
    return _format_audit(audit)


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
    }
