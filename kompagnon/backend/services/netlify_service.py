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
) -> dict:
    """
    Deployt HTML (+ optionales CSS / Redirects) als ZIP auf eine Netlify-Site.
    Rückgabe: { deploy_id, deploy_url, state }
    """
    default_headers = (
        "/*\n"
        "  X-Frame-Options: DENY\n"
        "  X-Content-Type-Options: nosniff"
    )

    # ZIP im Speicher aufbauen
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        full_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Website</title>
  {f'<link rel="stylesheet" href="/style.css">' if css else ''}
</head>
<body>
{html}
</body>
</html>"""

        zf.writestr("index.html", full_html)
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


def check_dns_active(domain: str, netlify_site_url: str = "") -> bool:
    """Prüft ob die Domain bereits auf Netlify zeigt.
    Netlify load-balancer IPs beginnen mit 75.2 oder 99.83.
    """
    import socket
    clean = (domain or "").lower().strip()
    if not clean:
        return False
    for host in (clean, f"www.{clean}" if not clean.startswith("www.") else clean):
        try:
            ip = socket.gethostbyname(host)
            if ip.startswith("75.2") or ip.startswith("99.83"):
                return True
        except Exception:
            continue
    return False


def generate_dns_guide(domain: str, netlify_site_url: str) -> dict:
    """Erzeugt die DNS-Einträge die der Kunde bei seinem Anbieter eintragen muss."""
    clean_domain = (domain or "").lower().strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]
    clean_domain = clean_domain.lstrip(".")

    netlify_host = (netlify_site_url or "").replace("https://", "").replace("http://", "").rstrip("/")
    if not netlify_host:
        netlify_host = "<ihre-netlify-subdomain>.netlify.app"

    return {
        "domain": clean_domain,
        "netlify_url": netlify_site_url,
        "records": [
            {
                "type":  "A",
                "name":  "@",
                "value": "75.2.60.5",
                "ttl":   "3600",
                "note":  "Hauptdomain (ohne www)",
            },
            {
                "type":  "CNAME",
                "name":  "www",
                "value": netlify_host,
                "ttl":   "3600",
                "note":  "www-Subdomain",
            },
        ],
        "instructions": (
            f"Bitte loggen Sie sich bei Ihrem Domain-Anbieter "
            f"(z.B. IONOS, Strato, united-domains, GoDaddy) ein und tragen Sie "
            f"die folgenden DNS-Einträge für '{clean_domain}' ein. "
            f"Die Änderungen werden innerhalb von 1–48 Stunden aktiv. "
            f"Wir informieren Sie automatisch, sobald Ihre Website live ist."
        ),
    }


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
