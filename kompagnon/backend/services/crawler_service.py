"""
Website crawler for KOMPAGNON.
crawl_website(start_url, max_pages) follows internal links via async httpx.
"""
import asyncio
import time
from urllib.parse import urljoin, urlparse
from typing import List, Dict

try:
    import httpx
except ImportError:
    httpx = None

CRAWLER_UA = "KOMPAGNON-Crawler/1.0"
TIMEOUT = 10.0


def _same_domain(base: str, url: str) -> bool:
    return urlparse(base).netloc == urlparse(url).netloc


def _normalize(url: str) -> str:
    """Remove fragment and trailing slash for deduplication."""
    p = urlparse(url)
    return p._replace(fragment='').geturl().rstrip('/')


async def _fetch(client: "httpx.AsyncClient", url: str, depth: int) -> Dict:
    t0 = time.monotonic()
    try:
        resp = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
        load_time = round(time.monotonic() - t0, 3)
        body = resp.text if resp.headers.get('content-type', '').startswith('text/html') else ''
        return {'url': url, 'status_code': resp.status_code, 'depth': depth, 'load_time': load_time, 'body': body}
    except Exception:
        load_time = round(time.monotonic() - t0, 3)
        return {'url': url, 'status_code': None, 'depth': depth, 'load_time': load_time, 'body': ''}


def _extract_links(base_url: str, html: str) -> List[str]:
    """Extract internal <a href> links from raw HTML (no external dependency)."""
    import re
    links = []
    for m in re.finditer(r'href=["\']([^"\'#?]+)', html, re.IGNORECASE):
        href = m.group(1).strip()
        if not href or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        full = urljoin(base_url, href)
        if _same_domain(base_url, full):
            links.append(_normalize(full))
    return links


async def _crawl_async(start_url: str, max_pages: int) -> List[Dict]:
    if httpx is None:
        raise RuntimeError("httpx not installed — run: pip install httpx")

    visited = set()
    queue = [(start_url, 0)]
    results = []

    async with httpx.AsyncClient(headers={'User-Agent': CRAWLER_UA}, follow_redirects=True, timeout=TIMEOUT) as client:
        while queue and len(results) < max_pages:
            batch = queue[:5]
            queue = queue[5:]

            tasks = []
            for url, depth in batch:
                norm = _normalize(url)
                if norm in visited:
                    continue
                visited.add(norm)
                tasks.append(_fetch(client, url, depth))

            if not tasks:
                continue

            fetched = await asyncio.gather(*tasks)
            for item in fetched:
                body = item.pop('body', '')
                results.append(item)
                if item['status_code'] == 200 and len(results) < max_pages:
                    for link in _extract_links(item['url'], body):
                        if link not in visited and len(visited) < max_pages * 2:
                            queue.append((link, item['depth'] + 1))

    return results


def crawl_website(start_url: str, max_pages: int = 50) -> List[Dict]:
    """
    Synchronous entry point.
    Returns list of {url, status_code, depth, load_time}.
    """
    return asyncio.run(_crawl_async(start_url, max_pages))
