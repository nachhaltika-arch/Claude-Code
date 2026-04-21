"""
Netlify-Anbindung für KOMPAGNON
Funktionen: Site erstellen, HTML deployen, Domain setzen, Status, Löschen
"""
import httpx
import os
import zipfile
import io
import json
import logging
import re

logger = logging.getLogger(__name__)

NETLIFY_TOKEN = os.getenv("NETLIFY_API_TOKEN", "")
NETLIFY_API   = "https://api.netlify.com/api/v1"
HEADERS       = {
    "Authorization": f"Bearer {NETLIFY_TOKEN}",
    "Content-Type":  "application/json",
}


def _build_full_html(
    page_name: str,
    html: str,
    css: str,
    meta_description: str = "",
    company_name: str = "",
) -> str:
    title = f"{page_name} — {company_name}" if company_name and page_name else (page_name or company_name or "Website")
    meta_desc = meta_description or (f"{page_name} — {company_name}" if page_name else "")

    style_block = f"<style>\n{css.strip()}\n</style>" if css and css.strip() else ""
    meta_desc_tag = f'<meta name="description" content="{meta_desc}">' if meta_desc else ""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  {meta_desc_tag}
  {style_block}
</head>
<body>
{html}
</body>
</html>"""


def _slug(name: str) -> str:
    """Firmenname → netlify-kompatibler Site-Slug (lowercase, a-z 0-9 -)"""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:63] or "kompagnon-site"


async def create_site(site_name: str) -> dict:
    """
    Legt eine neue Netlify-Site an.
    site_name: Firmenname (wird automatisch in Slug umgewandelt)
    Rückgabe: { site_id, site_url, admin_url }
    """
    slug = _slug(site_name)
    payload = {"name": slug, "custom_domain": None}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{NETLIFY_API}/sites",
            headers=HEADERS,
            json=payload,
        )

    if not resp.is_success:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise Exception(f"Netlify Fehler ({resp.status_code}): {detail}")

    data = resp.json()
    return {
        "site_id":   data["id"],
        "site_url":  data.get("url") or data.get("ssl_url") or "",
        "admin_url": data.get("admin_url", ""),
    }


async def deploy_html(
    site_id: str,
    html: str,
    css: str = "",
    redirects: str = "",
    page_name: str = "",
    company_name: str = "",
    meta_description: str = "",
) -> dict:
    """
    Deployt HTML (+ optionales CSS / Redirects) als ZIP auf eine Netlify-Site.
    Wraps raw GrapesJS body-only HTML in a full DOCTYPE document.
    Rückgabe: { deploy_id, deploy_url, state }
    """
    if html and not html.strip().lower().startswith("<!doctype"):
        html = _build_full_html(
            page_name=page_name or "Website",
            html=html,
            css=css,
            meta_description=meta_description,
            company_name=company_name,
        )
        css = ""

    default_headers = (
        "/*\n"
        "  X-Frame-Options: DENY\n"
        "  X-Content-Type-Options: nosniff"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html)
        if css:
            zf.writestr("style.css", css)
        zf.writestr(
            "_redirects",
            redirects if redirects else "/*  /index.html  200",
        )
        zf.writestr("_headers", default_headers)
    zip_bytes = buf.getvalue()

    deploy_headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type":  "application/zip",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{NETLIFY_API}/sites/{site_id}/deploys",
            headers=deploy_headers,
            content=zip_bytes,
        )

    if not resp.is_success:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise Exception(f"Netlify Deploy Fehler ({resp.status_code}): {detail}")

    data = resp.json()
    return {
        "deploy_id":  data["id"],
        "deploy_url": data.get("deploy_ssl_url") or data.get("deploy_url") or "",
        "state":      data.get("state", "unknown"),
    }


async def set_custom_domain(site_id: str, domain: str) -> dict:
    """
    Setzt eine Custom-Domain auf der Netlify-Site.
    Rückgabe: { custom_domain, ssl_url, required_dns_record }
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{NETLIFY_API}/sites/{site_id}",
            headers=HEADERS,
            json={"custom_domain": domain},
        )

    if not resp.is_success:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise Exception(f"Netlify Domain Fehler ({resp.status_code}): {detail}")

    data = resp.json()
    dns_record = None
    if data.get("domain_aliases"):
        dns_record = f"CNAME {domain} → {data.get('name', '')}.netlify.app"

    return {
        "custom_domain":       data.get("custom_domain", domain),
        "ssl_url":             data.get("ssl_url", ""),
        "required_dns_record": dns_record,
    }


async def get_site_status(site_id: str) -> dict:
    """
    Ruft den aktuellen Status einer Netlify-Site ab.
    Rückgabe: { name, url, custom_domain, ssl, deploy_url, published_deploy }
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{NETLIFY_API}/sites/{site_id}",
            headers=HEADERS,
        )

    if not resp.is_success:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise Exception(f"Netlify Status Fehler ({resp.status_code}): {detail}")

    data = resp.json()
    published = data.get("published_deploy") or {}
    return {
        "name":             data.get("name", ""),
        "url":              data.get("url") or data.get("ssl_url") or "",
        "custom_domain":    data.get("custom_domain"),
        "ssl":              bool(data.get("ssl")),
        "deploy_url":       published.get("deploy_ssl_url") or published.get("deploy_url") or "",
        "published_deploy": {
            "id":         published.get("id"),
            "state":      published.get("state"),
            "created_at": published.get("created_at"),
        },
    }


async def delete_site(site_id: str) -> bool:
    """
    Löscht eine Netlify-Site dauerhaft.
    Rückgabe: True bei Erfolg
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.delete(
            f"{NETLIFY_API}/sites/{site_id}",
            headers=HEADERS,
        )

    if resp.status_code == 404:
        logger.warning(f"Netlify: Site {site_id} nicht gefunden (bereits gelöscht?)")
        return True
    if not resp.is_success:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise Exception(f"Netlify Löschen Fehler ({resp.status_code}): {detail}")

    return True


def generate_redirects(old_urls: list, new_urls: dict) -> str:
    """
    Erzeugt den Inhalt einer Netlify _redirects Datei.
    old_urls: Liste alter Pfade (z.B. ['/kontakt.html'])
    new_urls: Dict alter Pfad → neuer Pfad (z.B. {'/kontakt.html': '/kontakt'})
    SPA-Fallback wird immer am Ende eingefügt.
    """
    lines = []
    for url in old_urls:
        if url not in new_urls:
            continue
        target = new_urls[url] or "/"
        lines.append(f"{url}  {target}  301")
    # SPA-Fallback
    lines.append("/*  /index.html  200")
    return "\n".join(lines)


def generate_datenschutz_absatz() -> str:
    """
    Gibt einen fertigen deutschen Datenschutz-Absatz für Netlify-Hosting zurück.
    """
    return (
        "Diese Website wird gehostet von Netlify, Inc., 2325 3rd Street, "
        "Suite 296, San Francisco, CA 94107, USA. Netlify verarbeitet beim "
        "Abruf dieser Website technisch notwendige Daten wie IP-Adressen "
        "in Server-Logs (Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO). "
        "Mit Netlify besteht ein Auftragsverarbeitungsvertrag gemäß "
        "Art. 28 DSGVO. Netlify ist unter dem EU-US Data Privacy Framework "
        "zertifiziert. Weitere Informationen: https://www.netlify.com/privacy/"
    )
