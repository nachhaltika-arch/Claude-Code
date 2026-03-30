"""
Lead enrichment service — auto-scrapes website data and computes quality scores.
Reuses services/scraper.py for HTML extraction.
"""
import os
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


async def enrich_lead(lead_id: int, db) -> dict:
    """Enrich a single lead: scrape website, get PageSpeed, compute score."""
    from database import Lead
    from services.scraper import scrape_website

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or not lead.website_url:
        return {"status": "skipped", "reason": "Keine Website"}

    url = lead.website_url
    if not url.startswith("http"):
        url = "https://" + url

    enriched = {}

    # 1. Scrape website using existing scraper
    scraped = await scrape_website(url)

    if not lead.company_name or lead.company_name == "Unbekannt":
        if scraped.get("company_name"):
            enriched["company_name"] = scraped["company_name"]
    if not lead.phone and scraped.get("phone"):
        enriched["phone"] = scraped["phone"]
    if not lead.email and scraped.get("email"):
        enriched["email"] = scraped["email"]
    if not lead.city and scraped.get("city"):
        enriched["city"] = scraped["city"]
    if (not lead.trade or lead.trade == "Sonstiges") and scraped.get("trade") and scraped["trade"] != "Sonstiges":
        enriched["trade"] = scraped["trade"]

    has_ssl = url.startswith("https")
    has_impressum = scraped.get("has_impressum", False)

    # 2. PageSpeed score
    pagespeed_score = 0
    try:
        api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
        ps_url = (
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url={url}&strategy=mobile"
            + (f"&key={api_key}" if api_key else "")
        )
        async with httpx.AsyncClient(timeout=12.0) as client:
            ps_resp = await client.get(ps_url)
            ps_data = ps_resp.json()
            raw = ps_data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 0)
            pagespeed_score = int((raw or 0) * 100)
    except Exception:
        pass

    # 3. Compute analysis score (0-100)
    score = 0
    if has_ssl:
        score += 20
    if has_impressum:
        score += 15
    if enriched.get("email") or lead.email:
        score += 10
    if enriched.get("phone") or lead.phone:
        score += 10
    if pagespeed_score > 70:
        score += 25
    elif pagespeed_score > 50:
        score += 15
    elif pagespeed_score > 0:
        score += 5
    if enriched.get("city") or lead.city:
        score += 10
    if lead.website_url:
        score += 10

    geo_score = min(10, score // 10)

    # 4. Update lead
    try:
        for key, value in enriched.items():
            if value:
                setattr(lead, key, value)

        lead.analysis_score = score
        lead.geo_score = geo_score

        note = (
            f"[Auto-Enrichment] SSL: {'OK' if has_ssl else 'FEHLT'} | "
            f"Impressum: {'OK' if has_impressum else 'FEHLT'} | "
            f"PageSpeed: {pagespeed_score}/100 | Score: {score}/100"
        )
        lead.notes = (note + "\n" + lead.notes) if lead.notes else note

        db.commit()
    except Exception as e:
        db.rollback()
        return {"status": "error", "reason": str(e)}

    return {
        "status": "success",
        "enriched_fields": list(enriched.keys()),
        "analysis_score": score,
        "pagespeed_score": pagespeed_score,
        "has_ssl": has_ssl,
        "has_impressum": has_impressum,
    }


async def enrich_all_pending(db) -> dict:
    """Batch-enrich all leads with analysis_score=0 and a website URL."""
    from database import Lead

    pending = (
        db.query(Lead)
        .filter(Lead.analysis_score == 0, Lead.website_url != "", Lead.website_url != None)
        .limit(50)
        .all()
    )

    results = {"total": len(pending), "success": 0, "failed": 0, "skipped": 0}

    for lead in pending:
        try:
            result = await enrich_lead(lead.id, db)
            if result["status"] == "success":
                results["success"] += 1
            elif result["status"] == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1
            await asyncio.sleep(1)
        except Exception as e:
            results["failed"] += 1
            logger.error(f"Enrichment error lead {lead.id}: {e}")

    return results


def enrich_lead_sync(lead_id: int):
    """Sync wrapper for FastAPI BackgroundTasks."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        asyncio.run(enrich_lead(lead_id, db))
    except Exception as e:
        logger.error(f"Enrichment background error lead {lead_id}: {e}")
    finally:
        db.close()
