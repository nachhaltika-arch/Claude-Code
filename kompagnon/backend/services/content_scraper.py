"""
Content scraper — extrahiert strukturierten Content pro Seite.
scrape_page_content(url) → dict   (basic: title, h1, h2, paragraphs, contact)
scrape_page_full(url) → dict      (full: SEO, headings, text, assets, links)
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


async def scrape_page_full(url: str) -> dict:
    """Full single-page analysis: SEO, headings, text, assets, links."""
    from urllib.parse import urljoin, urlparse
    from datetime import datetime

    def _abs(base, href):
        if not href or href.startswith('data:'):
            return None
        return urljoin(base, href)

    if not httpx or not BeautifulSoup:
        return {"url": url, "error": "httpx or bs4 not available"}

    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": UA}, timeout=15.0, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception as e:
        return {"url": url, "error": str(e), "status_code": 0}

    soup = BeautifulSoup(resp.text, "html.parser")
    domain = urlparse(url).netloc

    # --- SEO ---
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    def _meta(name=None, prop=None):
        tag = soup.find("meta", attrs={"name": name} if name else {"property": prop})
        return tag.get("content", "").strip() if tag else ""
    meta_desc = _meta(name="description")
    canonical = soup.find("link", attrs={"rel": "canonical"})
    robots = soup.find("meta", attrs={"name": "robots"})
    lang = soup.find("html").get("lang", "") if soup.find("html") else ""

    og = {k: _meta(prop=f"og:{k}") for k in ["title", "description", "image", "url", "type", "site_name"]}
    schema_data = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            schema_data.append(json.loads(s.string))
        except Exception:
            pass

    # --- Headings ---
    headings = {}
    for lvl in ["h1", "h2", "h3", "h4"]:
        headings[lvl] = [h.get_text(strip=True) for h in soup.find_all(lvl) if h.get_text(strip=True)]

    # --- Links ---
    internal, external = [], []
    for a in soup.find_all("a", href=True):
        href = _abs(url, a.get("href", ""))
        if not href:
            continue
        entry = {"url": href, "text": a.get_text(strip=True)[:100]}
        if urlparse(href).netloc == domain:
            internal.append(entry)
        elif href.startswith("http"):
            external.append(entry)

    # --- Text ---
    for tag in soup(["script", "style", "noscript", "iframe", "nav", "footer"]):
        tag.decompose()
    full_text = re.sub(r"\n{3,}", "\n\n", soup.get_text(separator="\n", strip=True)).strip()
    word_count = len(full_text.split())

    # --- Assets ---
    images = []
    for img in soup.find_all("img"):
        src = _abs(url, img.get("src") or img.get("data-src") or "")
        if src:
            images.append({
                "url": src, "alt": img.get("alt", ""),
                "has_alt": bool(img.get("alt", "").strip()),
                "width": img.get("width"), "height": img.get("height"),
            })
    stylesheets = [
        {"url": _abs(url, l.get("href")), "media": l.get("media", "all")}
        for l in soup.find_all("link", rel=lambda r: r and "stylesheet" in r)
        if _abs(url, l.get("href"))
    ]
    scripts = [
        {"url": _abs(url, s.get("src")), "async": s.has_attr("async"), "defer": s.has_attr("defer")}
        for s in soup.find_all("script", src=True)
        if _abs(url, s.get("src"))
    ]
    fonts = []
    for l in soup.find_all("link"):
        href = l.get("href", "")
        if "fonts.googleapis" in href or "typekit" in href or (l.get("as") == "font"):
            fonts.append({"url": _abs(url, href) or href})

    # --- Favicon ---
    favicon = None
    for rel in ["icon", "shortcut icon"]:
        ft = soup.find("link", rel=lambda r: r and rel in " ".join(r).lower())
        if ft:
            favicon = _abs(url, ft.get("href"))
            break

    # --- Contact ---
    text_blob = soup.get_text(" ", strip=True)
    phone, email, address = "", "", ""
    for p in PHONE_PATTERNS:
        m = re.search(p, text_blob, re.I)
        if m:
            phone = re.sub(r"\s+", " ", m.group(1).strip())[:30]
            break
    em = re.findall(EMAIL_PATTERN, text_blob)
    if em:
        pref = [e for e in em if any(x in e.lower() for x in ["info", "kontakt", "contact", "mail"])]
        email = pref[0] if pref else em[0]
    am = re.search(ADDRESS_PATTERN, text_blob)
    if am:
        address = f"{am.group(1)} {am.group(2)}"

    return {
        "url": url,
        "status_code": resp.status_code,
        "crawled_at": datetime.utcnow().isoformat(),
        "seo": {
            "title": title, "title_length": len(title),
            "meta_description": meta_desc, "meta_description_length": len(meta_desc),
            "meta_keywords": _meta(name="keywords"),
            "meta_robots": robots.get("content") if robots else None,
            "canonical_url": canonical.get("href") if canonical else None,
            "language": lang, "open_graph": og, "schema_org": schema_data,
            "headings": headings,
        },
        "links": {
            "internal": internal[:30], "external": external[:30],
            "internal_count": len(internal), "external_count": len(external),
        },
        "text": {"full_text": full_text, "word_count": word_count, "char_count": len(full_text)},
        "assets": {
            "favicon": favicon, "images": images, "stylesheets": stylesheets,
            "scripts": scripts, "fonts": fonts,
            "summary": {
                "image_count": len(images), "images_without_alt": sum(1 for i in images if not i["has_alt"]),
                "stylesheet_count": len(stylesheets), "script_count": len(scripts), "font_count": len(fonts),
            },
        },
        "contact": {"phone": phone, "email": email, "address": address},
    }
