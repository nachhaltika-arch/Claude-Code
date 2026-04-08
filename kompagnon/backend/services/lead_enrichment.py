"""
Lead enrichment service — auto-scrapes website data and computes quality scores.
Reuses services/scraper.py for HTML extraction.
"""
import os
import asyncio
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_google_business_profile(
    company_name: str,
    city: str = "",
) -> dict:
    """
    Prüft ob ein Google Business Profil existiert.
    Nutzt Google Places Text Search API.
    Gibt dict zurück: claimed, place_id, rating, ratings_total
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")

    if not api_key or not company_name:
        return {"claimed": False, "place_id": None,
                "rating": None, "ratings_total": None}

    query = f"{company_name} {city}".strip()

    try:
        url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input":     query,
            "inputtype": "textquery",
            "fields":    "name,place_id,rating,user_ratings_total",
            "key":       api_key,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)

        if resp.status_code != 200:
            logger.warning(f"GBP API HTTP {resp.status_code} für {query}")
            return {"claimed": False, "place_id": None,
                    "rating": None, "ratings_total": None}

        data       = resp.json()
        status     = data.get("status", "")
        candidates = data.get("candidates", [])

        if status == "OK" and candidates:
            c = candidates[0]
            return {
                "claimed":       True,
                "place_id":      c.get("place_id"),
                "rating":        c.get("rating"),
                "ratings_total": c.get("user_ratings_total"),
            }

        if status == "REQUEST_DENIED":
            logger.warning(
                "GBP API: REQUEST_DENIED — "
                "Places API für diesen Key aktivieren: "
                "https://console.cloud.google.com/apis/library/"
                "places-backend.googleapis.com"
            )

        return {"claimed": False, "place_id": None,
                "rating": None, "ratings_total": None}

    except Exception as e:
        logger.warning(f"GBP Check Fehler für {query}: {e}")
        return {"claimed": False, "place_id": None,
                "rating": None, "ratings_total": None}


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

    # Favicon — Google Favicon API (reliable, no direct download needed)
    try:
        base_url = url.rstrip('/')
        domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        favicon_url = f'https://www.google.com/s2/favicons?domain={domain}&sz=64'
        # Try HTML-based fallback first if homepage HTML is available
        try:
            from services.impressum_scraper import extract_favicon_from_html
            html_favicon = extract_favicon_from_html(scraped.get('raw_html', ''), base_url)
            if html_favicon:
                favicon_url = html_favicon
        except Exception:
            pass
        enriched['favicon_url'] = favicon_url
    except Exception:
        pass

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

    # 2. North Data — Geschäftsführer lookup
    try:
        from northdata import fetch_geschaeftsfuehrer
        company = enriched.get("company_name") or lead.company_name or ""
        city = enriched.get("city") or lead.city or ""
        if company and not lead.geschaeftsfuehrer:
            gf = await fetch_geschaeftsfuehrer(company, city)
            if gf:
                enriched["geschaeftsfuehrer"] = gf
    except Exception as exc:
        logger.debug("NorthData enrichment skipped: %s", exc)

    # 3. PageSpeed score
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

    # 3b. Google Business Profile Check
    gbp = {"claimed": False, "place_id": None, "rating": None, "ratings_total": None}
    try:
        company  = enriched.get("company_name") or lead.company_name or ""
        city_val = enriched.get("city") or lead.city or ""
        already_checked = (
            lead.gbp_checked_at is not None
            and (datetime.utcnow() - lead.gbp_checked_at).days < 7
        )
        if not already_checked and company:
            gbp = await check_google_business_profile(company, city_val)
    except Exception as e:
        logger.warning(f"GBP Check übersprungen: {e}")

    # 4. Compute analysis score (0-100)
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

    # 5. Update lead
    try:
        for key, value in enriched.items():
            if value:
                setattr(lead, key, value)

        lead.analysis_score    = score
        lead.geo_score         = geo_score
        lead.gbp_place_id      = gbp.get("place_id")
        lead.gbp_claimed       = gbp.get("claimed", False)
        lead.gbp_rating        = gbp.get("rating")
        lead.gbp_ratings_total = gbp.get("ratings_total")
        lead.gbp_checked_at    = datetime.utcnow()

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
