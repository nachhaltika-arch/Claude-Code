"""
Content scraper — extrahiert strukturierten Content pro Seite.
scrape_page_content(url) → dict
scrape_all_pages(website_url, max_pages) → list[dict]
"""
import re
import json
import asyncio

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from services.crawler_service import crawl_website

UA      = "KOMPAGNON-ContentBot/1.0"
TIMEOUT = 8.0

PHONE_PATTERNS = [
    r'(?:Tel|Telefon|Phone|Fon|Ruf)[\s.:]*(\+?[\d\s\-\/\(\)]{8,20})',
    r'(\+49[\s\-\d]{8,20})',
    r'(0[\d]{2,5}[\s\-\/][\d\s\-]{4,15})',
]
EMAIL_PATTERN   = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
ADDRESS_PATTERN = r'\b(\d{5})\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s[A-ZÄÖÜ][a-zäöüß]+)?)'


async def scrape_page_content(url: str) -> dict:
    """Fetch one URL and extract structured content."""
    result = {"url": url}
    if not httpx or not BeautifulSoup:
        return result
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": UA},
            timeout=TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        # page_title
        title_tag = soup.find("title")
        result["page_title"] = title_tag.get_text(strip=True)[:200] if title_tag else ""

        # meta_description
        meta = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        result["meta_description"] = (meta.get("content", "")[:300] if meta else "")

        # h1
        h1 = soup.find("h1")
        result["h1"] = h1.get_text(strip=True)[:200] if h1 else ""

        # h2_list (max 10)
        h2s = [tag.get_text(strip=True) for tag in soup.find_all("h2")][:10]
        result["h2_list"] = json.dumps(h2s, ensure_ascii=False)

        # paragraphs — p-Tags mit mehr als 40 Zeichen (max 20)
        paras = [
            p.get_text(strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) > 40
        ][:20]
        result["paragraphs"] = json.dumps(paras, ensure_ascii=False)

        # images (max 20)
        imgs = [
            {"src": img.get("src", ""), "alt": img.get("alt", "")}
            for img in soup.find_all("img")
            if img.get("src")
        ][:20]
        result["images"] = json.dumps(imgs, ensure_ascii=False)

        # contact_phone
        for pattern in PHONE_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                result["contact_phone"] = re.sub(r"\s+", " ", m.group(1).strip())[:30]
                break

        # contact_email
        emails = re.findall(EMAIL_PATTERN, text)
        if emails:
            preferred = [
                e for e in emails
                if any(p in e.lower() for p in ["info", "kontakt", "contact", "mail", "office", "hallo"])
            ]
            result["contact_email"] = preferred[0] if preferred else emails[0]

        # contact_address (PLZ + Ort)
        m = re.search(ADDRESS_PATTERN, text)
        if m:
            result["contact_address"] = f"{m.group(1)} {m.group(2)}".strip()

    except Exception:
        pass  # Leeres dict mit url zurückgeben, nicht abbrechen

    return result


async def scrape_all_pages(website_url: str, max_pages: int = 20) -> list:
    """Crawl up to max_pages URLs, then scrape each one for content."""
    try:
        crawled = crawl_website(website_url, max_pages=max_pages)
        urls = [item["url"] for item in crawled if item.get("url")]
    except Exception:
        urls = [website_url]

    tasks = [scrape_page_content(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return list(results)
