"""
WordPress REST API helper — connection test and Elementor page push.
Uses Application Passwords (WP 5.6+) for Basic Auth.
"""
import json
import logging
from base64 import b64encode
import httpx

logger = logging.getLogger(__name__)


def _basic_header(username: str, app_password: str) -> dict:
    token = b64encode(f"{username}:{app_password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def test_wp_connection(url: str, username: str, app_password: str) -> tuple[bool, str]:
    """
    Test a WordPress REST API connection.
    Returns (True, "") on success or (False, error_message).
    """
    endpoint = f"{url.rstrip('/')}/wp-json/wp/v2/users/me"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(endpoint, headers=_basic_header(username, app_password))
        if resp.status_code == 200:
            return True, ""
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        return False, body.get("message") or f"HTTP {resp.status_code}"
    except Exception as exc:
        logger.debug("WP connection test failed for %s: %s", url, exc)
        return False, str(exc)


async def push_to_wordpress(
    url: str,
    username: str,
    app_password: str,
    html: str,
    css: str,
    page_title: str,
) -> tuple[bool, str]:
    """
    Create a draft WordPress page with a self-contained HTML document as content.
    Returns (True, page_url) on success or (False, error_message).
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
        "content": full_html,
        "status": "draft",
    }
    endpoint = f"{url.rstrip('/')}/wp-json/wp/v2/pages"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                endpoint,
                json=payload,
                headers=_basic_header(username, app_password),
            )
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code in (200, 201):
            return True, data.get("link", "")
        return False, data.get("message") or f"HTTP {resp.status_code}"
    except Exception as exc:
        logger.debug("WP push failed for %s: %s", url, exc)
        return False, str(exc)


async def push_to_wordpress_elementor(
    url: str,
    username: str,
    app_password: str,
    html: str,
    page_title: str,
) -> tuple[bool, str]:
    """
    Create a draft WordPress page with the HTML wrapped in an Elementor HTML widget.
    Returns (True, page_url) on success or (False, error_message).
    """
    elementor_data = [
        {
            "id": "ks1section",
            "elType": "section",
            "settings": {},
            "elements": [
                {
                    "id": "ks1column",
                    "elType": "column",
                    "settings": {"_column_size": 100},
                    "elements": [
                        {
                            "id": "ks1widget",
                            "elType": "widget",
                            "widgetType": "html",
                            "settings": {"html": html},
                            "elements": [],
                        }
                    ],
                }
            ],
        }
    ]

    payload = {
        "title": page_title,
        "status": "draft",
        "meta": {
            "_elementor_edit_mode": "builder",
            "_elementor_data": json.dumps(elementor_data),
            "_elementor_template_type": "wp-page",
        },
    }

    endpoint = f"{url.rstrip('/')}/wp-json/wp/v2/pages"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                endpoint,
                json=payload,
                headers=_basic_header(username, app_password),
            )
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code in (200, 201):
            return True, data.get("link", "")
        return False, data.get("message") or f"HTTP {resp.status_code}"
    except Exception as exc:
        logger.debug("WP Elementor push failed for %s: %s", url, exc)
        return False, str(exc)
