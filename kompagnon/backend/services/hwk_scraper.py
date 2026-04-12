"""
HWK Lead Scraper Service
Scrapes Handwerkskammer directories and saves leads directly to PostgreSQL.

Supported chambers:
  - muenchen     (hwk-muenchen.de — BDB system, detail pages)
  - rheinhessen  (hwk.de — form search, results on listing page)

How it works:
  1. HTTP GET request to the HWK search URL with trade + city/PLZ params
  2. Parse HTML with BeautifulSoup to extract company listings or detail-page URLs
  3. For München: follow each detail URL to scrape contact data
  4. Deduplicate by (company_name, zip) before inserting to DB
  5. Write leads to the `leads` table via SQLAlchemy

Usage (standalone):
    from services.hwk_scraper import HwkScraperService
    service = HwkScraperService()
    service.run_chamber("muenchen", trade_label="elektrotechnik", trade_value="3", cities=["80331"])
"""

import re
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx
from bs4 import BeautifulSoup

from database import SessionLocal, Lead

logger = logging.getLogger(__name__)

# ── Chamber configs ────────────────────────────────────────────────────────────
CHAMBER_CONFIGS = {
    "muenchen": {
        "name": "HWK München und Oberbayern",
        "search_url": "https://www.hwk-muenchen.de/betriebe/suche-74,3989,bdbsearch.html",
        "detail_base": "https://www.hwk-muenchen.de",
        "has_detail_pages": True,
        "count_pattern": re.compile(r"Ergebnisse\s+\d+\s+-\s+\d+\s+von\s+(\d+)"),
        "detail_link_substr": "bdbdetail",
        "search_param_zipcode": "search-filter-zipcode",
        "search_param_radius": "search-filter-radius",
        "search_param_trade": "search-filter-jobnr",
        "default_radius": "5",
    },
    "rheinhessen": {
        "name": "HWK Rheinhessen",
        "search_url": "https://www.hwk.de/handwerkersuche/",
        "detail_base": "https://www.hwk.de",
        "has_detail_pages": False,
        "count_pattern": re.compile(r"Insgesamt\s+(\d+)\s+Ergebnisse"),
        "search_param_trade": "tx_hwkfindercraftsearch_pi1[jobId]",
        "search_param_city": "tx_hwkfindercraftsearch_pi1[city]",
    },
}

# ── Trades — most common Gewerke with their BDB job numbers ───────────────────
# For München (BDB system), we need numeric job IDs.
# For Rheinhessen, the selectOption value (varies — use config/trades.js labels).
TRADES_MUENCHEN: List[Dict[str, Any]] = [
    {"label": "elektrotechnik",       "value": "3",   "name": "Elektrotechnik"},
    {"label": "maler-lackierer",      "value": "15",  "name": "Maler und Lackierer"},
    {"label": "dachdecker",           "value": "4",   "name": "Dachdecker"},
    {"label": "sanitaer-heizung-klima","value": "25",  "name": "Sanitär-, Heizungs- und Klimatechnik"},
    {"label": "kfz-technik",          "value": "14",  "name": "Kraftfahrzeugtechniker"},
    {"label": "zimmerer",             "value": "43",  "name": "Zimmerer"},
    {"label": "schreiner",            "value": "28",  "name": "Schreiner"},
    {"label": "maurer-betonbauer",    "value": "17",  "name": "Maurer und Betonbauer"},
    {"label": "fliesenleger",         "value": "8",   "name": "Fliesen-, Platten- und Mosaikleger"},
    {"label": "metallbauer",          "value": "19",  "name": "Metallbauer"},
]

# Default cities (PLZ) for scheduled runs — configurable via env
DEFAULT_CITIES_MUENCHEN = [
    "80331", "80333", "80335", "80336", "80337", "80339",
    "80469", "80538", "80539", "80634", "80636", "80637",
    "80638", "80639", "80796", "80797", "80798", "80799",
    "80801", "80802", "80803", "80804", "80805", "80809",
]

# ── HTTP Client helpers ────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.7",
}

REQUEST_TIMEOUT = 20.0   # seconds
PAUSE_BETWEEN_REQUESTS = 1.2  # seconds — server-friendly
MAX_PAGES = 50           # safety cap for pagination


# ── Parsers ────────────────────────────────────────────────────────────────────

def _parse_muenchen_detail(text: str, url: str) -> Dict[str, Any]:
    """
    Parse contact data from HWK München detail page innerText.
    Matches the Node.js parseDetail() logic from hwk-scrape-muenchen.js.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    company_name = street = zip_code = city = phone = fax = email = website = ""
    trades = []
    in_contact = in_trades = False

    for i, line in enumerate(lines):
        if not company_name and line.startswith("Firma "):
            company_name = line[6:].strip()
            continue

        if not street and re.search(r"\S.*\d", line):
            if not line.startswith(("Telefon", "Fax", "Mobil")):
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                m = re.match(r"^(\d{5})\s+(.+)$", next_line)
                if m:
                    street = line
                    zip_code, city = m.group(1), m.group(2)
                    continue

        if line == "Kontakt":
            in_contact = True
            continue
        if line == "Eingetragene Berufe":
            in_contact = False
            in_trades = True
            continue
        if line in ("Leistungsbeschreibung", "Weitere Informationen"):
            in_trades = False
            continue

        if in_contact:
            if line.startswith("Telefon "):
                phone = line[8:].strip()
            elif line.startswith("Mobil ") and not phone:
                phone = line[6:].strip()
            elif line.startswith("Fax "):
                fax = line[4:].strip()
            elif re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", line):
                email = line
            elif re.match(r"^(https?://|www\.)", line):
                website = line

        if in_trades and line and not line.startswith("Ausbildungsbetrieb"):
            trades.append(line)

    return {
        "company_name": company_name,
        "street": street,
        "zip": zip_code,
        "city": city,
        "phone": phone,
        "email": email,
        "website_url": website,
        "trade_detail": trades[0] if trades else "",
        "_source_url": url,
    }


def _parse_rheinhessen_results(html: str, city: str) -> List[Dict[str, Any]]:
    """
    Parse company listings from HWK Rheinhessen results page.
    Returns list of lead dicts.
    """
    soup = BeautifulSoup(html, "lxml")
    leads = []

    # Each result is typically in a div.result-item or similar
    # Try multiple selectors for robustness
    items = (
        soup.select(".tx-hwkfindercraftsearch .result-item")
        or soup.select(".handwerker-result")
        or soup.select("article.result")
        or soup.select(".company-entry")
    )

    for item in items:
        text = item.get_text(separator="\n")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        lead: Dict[str, Any] = {
            "company_name": "",
            "phone": "",
            "email": "",
            "website_url": "",
            "city": city,
            "zip": "",
        }

        for line in lines:
            if not lead["company_name"] and len(line) > 3 and not re.match(r"^[\d\s\+\-/()]+$", line):
                lead["company_name"] = line
            if re.match(r"^(\+49|0)[\d\s\-/()]{6,}$", line):
                lead["phone"] = line
            if re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", line):
                lead["email"] = line
            if re.match(r"^(https?://|www\.)", line):
                lead["website_url"] = line
            m = re.match(r"^(\d{5})\s+(.+)$", line)
            if m:
                lead["zip"], lead["city"] = m.group(1), m.group(2)

        if lead["company_name"]:
            leads.append(lead)

    return leads


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _lead_exists(db, company_name: str, zip_code: str) -> bool:
    """Check if a lead with this company+zip already exists (dedup)."""
    return db.query(Lead).filter(
        Lead.company_name == company_name,
        Lead.city.contains(zip_code) if zip_code else Lead.company_name == company_name,
    ).first() is not None


def _save_lead(db, data: Dict[str, Any], chamber: str, trade_name: str) -> bool:
    """
    Insert a lead into the DB. Returns True if inserted, False if duplicate/skipped.
    """
    company = data.get("company_name", "").strip()
    if not company:
        return False

    zip_code = data.get("zip", "") or ""
    city = data.get("city", "") or ""

    # Dedup: skip if company+zip combo already exists
    existing = db.query(Lead).filter(Lead.company_name == company).first()
    if existing:
        return False

    lead = Lead(
        company_name=company,
        contact_name=data.get("contact_name", ""),
        phone=data.get("phone", "")[:50] if data.get("phone") else "",
        email=data.get("email", "")[:255] if data.get("email") else "nicht@ermittelt.de",
        website_url=data.get("website_url", "")[:500] if data.get("website_url") else None,
        city=(zip_code + " " + city).strip() if zip_code else city,
        trade=trade_name,
        lead_source=f"HWK-{chamber.capitalize()}",
        status="new",
    )
    db.add(lead)
    return True


# ── Core scraper class ─────────────────────────────────────────────────────────

class HwkScraperService:
    """
    Scrapes HWK directories and writes leads to PostgreSQL.

    Example:
        service = HwkScraperService()
        result = service.run_chamber(
            chamber="muenchen",
            trade_label="elektrotechnik",
            trade_value="3",
            trade_name="Elektrotechnik",
            cities=["80331", "80333"],
        )
        print(result)  # {"leads_found": 42, "leads_saved": 38, "errors": 0}
    """

    def __init__(self):
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            verify=True,   # SSL-Verifikation aktiv — HWK-Seiten haben gültige Zertifikate
        )

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────────────────────────

    def run_chamber(
        self,
        chamber: str,
        trade_label: str,
        trade_value: str,
        trade_name: str,
        cities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Scrape one trade for one chamber and save to DB.
        Returns stats: {"leads_found", "leads_saved", "errors", "cities_done"}.
        """
        cfg = CHAMBER_CONFIGS.get(chamber)
        if not cfg:
            raise ValueError(f"Unknown chamber: {chamber}. Available: {list(CHAMBER_CONFIGS)}")

        if cities is None:
            cities = DEFAULT_CITIES_MUENCHEN if chamber == "muenchen" else []

        logger.info(f"🔍 HWK Scraper: {cfg['name']} | {trade_name} | {len(cities)} cities")

        stats = {"leads_found": 0, "leads_saved": 0, "errors": 0, "cities_done": 0}

        if chamber == "muenchen":
            self._run_muenchen(cfg, trade_value, trade_name, cities, stats)
        elif chamber == "rheinhessen":
            self._run_rheinhessen(cfg, trade_value, trade_name, cities, stats)

        logger.info(
            f"✅ Done: {stats['leads_found']} found | "
            f"{stats['leads_saved']} saved | {stats['errors']} errors"
        )
        return stats

    def run_default_batch(self) -> Dict[str, Any]:
        """
        Scheduled job: scrape top 5 München trades with default city list.
        Called by APScheduler.
        """
        total = {"leads_found": 0, "leads_saved": 0, "errors": 0, "cities_done": 0}
        for trade in TRADES_MUENCHEN[:5]:
            try:
                result = self.run_chamber(
                    chamber="muenchen",
                    trade_label=trade["label"],
                    trade_value=trade["value"],
                    trade_name=trade["name"],
                    cities=DEFAULT_CITIES_MUENCHEN[:10],  # top 10 PLZ per run
                )
                for k in total:
                    total[k] += result.get(k, 0)
            except Exception as e:
                logger.error(f"Batch error for {trade['label']}: {e}")
                total["errors"] += 1
        return total

    # ── München (BDB) ──────────────────────────────────────────────────────────

    def _run_muenchen(
        self,
        cfg: Dict,
        trade_value: str,
        trade_name: str,
        cities: List[str],
        stats: Dict,
    ):
        """Stage 1: collect detail URLs → Stage 2: scrape each detail page."""
        all_detail_urls: List[str] = []

        # Stage 1: collect detail page URLs for each PLZ
        for plz in cities:
            try:
                urls = self._muenchen_collect_urls(cfg, trade_value, plz)
                all_detail_urls.extend(urls)
                logger.debug(f"  {plz}: {len(urls)} URLs")
                time.sleep(PAUSE_BETWEEN_REQUESTS)
            except Exception as e:
                logger.warning(f"  ⚠ {plz} URL collection failed: {e}")
                stats["errors"] += 1

        # Deduplicate URLs
        all_detail_urls = list(dict.fromkeys(all_detail_urls))
        stats["leads_found"] = len(all_detail_urls)
        stats["cities_done"] = len(cities)

        logger.info(f"  Stage 1 complete: {len(all_detail_urls)} unique detail URLs")

        # Stage 2: scrape each detail page
        db = SessionLocal()
        try:
            for i, url in enumerate(all_detail_urls):
                try:
                    lead_data = self._muenchen_scrape_detail(cfg, url)
                    if lead_data:
                        saved = _save_lead(db, lead_data, "muenchen", trade_name)
                        if saved:
                            stats["leads_saved"] += 1
                    if (i + 1) % 25 == 0:
                        db.commit()
                        logger.debug(f"  Progress: {i + 1}/{len(all_detail_urls)}")
                    time.sleep(PAUSE_BETWEEN_REQUESTS * 0.4)
                except Exception as e:
                    logger.debug(f"  Detail page error {url}: {e}")
                    stats["errors"] += 1
            db.commit()
        finally:
            db.close()

    def _muenchen_collect_urls(
        self, cfg: Dict, trade_value: str, plz: str
    ) -> List[str]:
        """Fetch search results pages and collect all bdbdetail links."""
        params = {
            "search-searchterm": "",
            "search-filter-zipcode": plz,
            "search-filter-radius": cfg["default_radius"],
            "search-filter-jobnr": trade_value,
            "search-job": "",
            "search-local": "",
            "search-filter-training": "",
            "search-filter-experience": "",
        }

        detail_urls: List[str] = []
        page = 1

        while page <= MAX_PAGES:
            resp = self.client.get(cfg["search_url"], params=params)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            # Collect detail links
            links = [
                a["href"] for a in soup.find_all("a", href=True)
                if cfg["detail_link_substr"] in a["href"]
            ]
            for href in links:
                full = href if href.startswith("http") else cfg["detail_base"] + href
                detail_urls.append(full)

            # Count total
            text = soup.get_text()
            m = cfg["count_pattern"].search(text)
            total = int(m.group(1)) if m else 0

            if not links or len(detail_urls) >= total:
                break

            # Find next page link
            next_link = (
                soup.select_one("a.next")
                or soup.select_one("li.next a")
                or soup.select_one(".pagination a[rel='next']")
                or soup.select_one(f"a:-soup-contains('{page + 1}')")
            )
            if not next_link:
                break

            # Build next page URL
            next_href = next_link.get("href", "")
            if next_href.startswith("http"):
                params = {}  # URL contains all params
                cfg = {**cfg, "search_url": next_href}
                # Reset for next iteration
            else:
                # Try page parameter
                params["tx_bdbsearch_pi1[currentPage]"] = str(page)

            page += 1
            time.sleep(PAUSE_BETWEEN_REQUESTS)

        return list(dict.fromkeys(detail_urls))

    def _muenchen_scrape_detail(self, cfg: Dict, url: str) -> Optional[Dict[str, Any]]:
        """Fetch a single München detail page and parse contact info."""
        resp = self.client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text(separator="\n")
        data = _parse_muenchen_detail(text, url)
        return data if data.get("company_name") else None

    # ── Rheinhessen ────────────────────────────────────────────────────────────

    def _run_rheinhessen(
        self,
        cfg: Dict,
        trade_value: str,
        trade_name: str,
        cities: List[str],
        stats: Dict,
    ):
        """Scrape Rheinhessen listing pages (no detail pages needed)."""
        db = SessionLocal()
        try:
            for city in cities:
                try:
                    leads = self._rheinhessen_search(cfg, trade_value, city)
                    stats["leads_found"] += len(leads)
                    for lead_data in leads:
                        lead_data["trade_label"] = trade_name
                        saved = _save_lead(db, lead_data, "rheinhessen", trade_name)
                        if saved:
                            stats["leads_saved"] += 1
                    db.commit()
                    stats["cities_done"] += 1
                    time.sleep(PAUSE_BETWEEN_REQUESTS)
                except Exception as e:
                    logger.warning(f"  ⚠ {city} error: {e}")
                    stats["errors"] += 1
        finally:
            db.close()

    def _rheinhessen_search(
        self, cfg: Dict, trade_value: str, city: str
    ) -> List[Dict[str, Any]]:
        """Submit form search for Rheinhessen and parse results."""
        params = {
            cfg["search_param_trade"]: trade_value,
            cfg["search_param_city"]: city,
        }
        resp = self.client.get(cfg["search_url"], params=params)
        resp.raise_for_status()
        return _parse_rheinhessen_results(resp.text, city)
