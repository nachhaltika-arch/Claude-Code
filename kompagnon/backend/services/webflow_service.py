"""
Webflow API v2 helper — connection test and page push.
Uses a Webflow API token for Bearer Auth.
"""
import re
import logging
import httpx

logger = logging.getLogger(__name__)

_WEBFLOW_BASE = "https://api.webflow.com/v2"


def _auth_header(api_token: str) -> dict:
    return {"Authorization": f"Bearer {api_token}", "accept-version": "2.0.0"}


def _slugify(title: str) -> str:
    t = title.lower()
    t = t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    slug = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return slug or "page"


async def test_webflow_connection(api_token: str) -> tuple[bool, str]:
    """
    Verify the Webflow API token and return (True, info) or (False, error).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_WEBFLOW_BASE}/sites", headers=_auth_header(api_token))
        if resp.status_code == 200:
            sites = resp.json().get("sites", [])
            names = ", ".join(s.get("displayName", s.get("id", "?")) for s in sites[:3])
            return True, f"{len(sites)} Site(s): {names}" if sites else "Verbunden (keine Sites)"
        return False, f"HTTP {resp.status_code}"
    except Exception as exc:
        logger.debug("Webflow connection test failed: %s", exc)
        return False, str(exc)


async def push_to_webflow(
    api_token: str,
    site_id: str,
    html: str,
    css: str,
    page_title: str,
) -> tuple[bool, str]:
    """
    Create a draft Webflow page with a self-contained HTML document.
    Returns (True, page_url) or (False, error_message).
    """
    full_html = (
        f'<!DOCTYPE html><html lang="de"><head>'
        f'<meta charset="UTF-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{page_title}</title>'
        f'<style>{css}</style>'
        f'</head><body>{html}</body></html>'
    )
    payload = {
        "title": page_title,
        "slug": _slugify(page_title),
        "body": full_html,
        "isDraft": True,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_WEBFLOW_BASE}/sites/{site_id}/pages",
                json=payload,
                headers=_auth_header(api_token),
            )
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code in (200, 201):
            return True, data.get("url", "")
        return False, data.get("message") or f"HTTP {resp.status_code}"
    except Exception as exc:
        logger.debug("Webflow push failed for site %s: %s", site_id, exc)
        return False, str(exc)
