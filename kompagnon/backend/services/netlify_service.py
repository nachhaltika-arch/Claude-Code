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

NETLIFY_API = "https://api.netlify.com/api/v1"


def _get_netlify_token(token: str = None) -> str:
    """Token lazy aus Env laden. Wirft ValueError wenn leer.

    Grund fuer lazy loading: beim Modulimport war der Env-Wert unter Umstaenden
    noch nicht verfuegbar, was zu `Authorization: Bearer ` (leer!) fuehrte und
    httpx zum Crash ("Illegal header value") brachte.
    """
    t = (token or os.getenv("NETLIFY_API_TOKEN", "")).strip()
    if not t:
        raise ValueError(
            "NETLIFY_API_TOKEN ist nicht gesetzt. "
            "Bitte in Render.com unter Environment eintragen."
        )
    return t


def _get_headers(token: str = None) -> dict:
    """JSON-Header mit frisch geladenem Bearer-Token."""
    return {
        "Authorization": f"Bearer {_get_netlify_token(token)}",
        "Content-Type":  "application/json",
    }


# ── Security Headers fuer Netlify-Deployments ─────────────────────────────
# Wird als _headers-Datei im Deploy-ZIP mitgeschickt und von Netlify auf
# jede Response angewendet. Die CSP erlaubt legitime Drittanbieter
# (Google Analytics, GTM, Facebook Pixel, Trustpilot, YouTube-Embed)
# und blockiert alle anderen externen Script-Quellen.
SECURITY_HEADERS = (
    "/*\n"
    "  X-Frame-Options: SAMEORIGIN\n"
    "  X-Content-Type-Options: nosniff\n"
    "  Referrer-Policy: strict-origin-when-cross-origin\n"
    "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
    "  Content-Security-Policy: "
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' "
    "https://www.googletagmanager.com "
    "https://www.google-analytics.com "
    "https://connect.facebook.net "
    "https://widget.trustpilot.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https:; "
    "frame-src 'self' https://www.google.com https://www.youtube.com; "
    "connect-src 'self' https://www.google-analytics.com"
)


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
            headers=_get_headers(),
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
    page_title: str = "Website",
    meta_description: str = "",
    company_name: str = "",
) -> dict:
    """
    Deployt HTML (+ optionales CSS / Redirects) als ZIP auf eine Netlify-Site.
    Rückgabe: { deploy_id, deploy_url, state[, security_notice] }
    """
    # Script-/iFrame-Inhalte im Deploy dokumentieren
    script_count = len(re.findall(r'<script[\s>]', html or "", re.IGNORECASE))
    iframe_count = len(re.findall(r'<iframe[\s>]', html or "", re.IGNORECASE))

    # ZIP im Speicher aufbauen
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        og_description = meta_description or f"Offizielle Website von {company_name or page_title}"

        full_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{og_description}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{og_description}">
  <meta property="og:type" content="website">
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
        zf.writestr("_headers", SECURITY_HEADERS)
    zip_bytes = buf.getvalue()

    deploy_headers = {
        "Authorization": f"Bearer {_get_netlify_token()}",
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
    result = {
        "deploy_id":  data["id"],
        "deploy_url": data.get("deploy_ssl_url") or data.get("deploy_url") or "",
        "state":      data.get("state", "unknown"),
    }

    if script_count or iframe_count:
        result["security_notice"] = (
            f"Deploy enthaelt {script_count} Script(s) und "
            f"{iframe_count} iFrame(s). CSP-Header aktiv."
        )
        logger.warning(
            f"Deploy mit Script-Inhalt: site={site_id} | "
            f"scripts={script_count} | iframes={iframe_count}"
        )

    return result


async def deploy_all_pages(
    site_id: str,
    page_files: dict,
    shared_css: str = "",
    company_name: str = "Website",
) -> dict:
    """
    Deployt mehrere Seiten als ZIP auf Netlify (Multi-Page Deploy).

    page_files: dict mapping filename -> { html, css, page_title, meta_desc }
        Beispiel:
            {
                "index.html":           { html, css, page_title, meta_desc },
                "leistungen/index.html": { html, css, page_title, meta_desc },
            }
    shared_css: optional — zusammengefuehrtes CSS aller Seiten (wird als /style.css
                verlinkt wenn vorhanden)
    company_name: Fallback fuer Meta-Tags

    Rueckgabe: { deploy_id, deploy_url, state[, security_notice] }
    """
    # Script-/iFrame-Inhalte ueber ALLE Seiten zaehlen
    script_count = 0
    iframe_count = 0
    for _pf in page_files.values():
        _html = _pf.get("html", "") or ""
        script_count += len(re.findall(r'<script[\s>]', _html, re.IGNORECASE))
        iframe_count += len(re.findall(r'<iframe[\s>]', _html, re.IGNORECASE))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        for filename, page in page_files.items():
            page_title = page.get("page_title") or company_name
            og_desc    = page.get("meta_desc") or f"Offizielle Website von {company_name}"
            css_link   = '<link rel="stylesheet" href="/style.css">' if shared_css else ''
            full_html  = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{og_desc}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:type" content="website">
  {css_link}
</head>
<body>
{page.get('html', '')}
</body>
</html>"""
            zf.writestr(filename, full_html)

        if shared_css:
            zf.writestr("style.css", shared_css)

        # Keine SPA-Redirect-Regel — echte Dateien fuer echte Pfade
        zf.writestr("_redirects", "")
        zf.writestr("_headers", SECURITY_HEADERS)

    zip_bytes = buf.getvalue()

    deploy_headers = {
        "Authorization": f"Bearer {_get_netlify_token()}",
        "Content-Type":  "application/zip",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
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
        raise Exception(f"Netlify Multi-Page Deploy Fehler ({resp.status_code}): {detail}")

    data = resp.json()
    result = {
        "deploy_id":  data["id"],
        "deploy_url": data.get("deploy_ssl_url") or data.get("deploy_url") or "",
        "state":      data.get("state", "unknown"),
    }

    if script_count or iframe_count:
        result["security_notice"] = (
            f"Deploy enthaelt {script_count} Script(s) und "
            f"{iframe_count} iFrame(s). CSP-Header aktiv."
        )
        logger.warning(
            f"Multi-page deploy mit Script-Inhalt: site={site_id} | "
            f"pages={len(page_files)} | scripts={script_count} | iframes={iframe_count}"
        )

    return result


async def set_custom_domain(site_id: str, domain: str) -> dict:
    """
    Setzt eine Custom-Domain auf der Netlify-Site.
    Rückgabe: { custom_domain, ssl_url, required_dns_record }
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{NETLIFY_API}/sites/{site_id}",
            headers=_get_headers(),
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
            headers=_get_headers(),
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
            headers=_get_headers(),
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


def generate_dns_guide(domain: str, netlify_site_url: str,
                       email_forwarding: list = None) -> dict:
    """Erzeugt DNS-Eintraege + optionale E-Mail-Weiterleitungen."""
    clean_domain = (domain or "").lower().strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]
    clean_domain = clean_domain.lstrip(".")

    netlify_host = (netlify_site_url or "").replace("https://", "").replace("http://", "").rstrip("/")
    if not netlify_host:
        netlify_host = "<ihre-netlify-subdomain>.netlify.app"

    records = [
        {"type": "A", "name": "@", "value": "75.2.60.5", "ttl": "3600",
         "note": "Hauptdomain (ohne www)", "category": "website"},
        {"type": "CNAME", "name": "www", "value": netlify_host, "ttl": "3600",
         "note": "www-Subdomain", "category": "website"},
    ]

    email_records = []
    if email_forwarding:
        seen_mx = False
        for fwd in email_forwarding:
            alias = fwd.get("alias", "info")
            ziel  = fwd.get("ziel", "")
            if not ziel:
                continue
            if not seen_mx:
                email_records.append({"type": "MX", "name": "@", "value": "mx1.forwardemail.net",
                                      "priority": "10", "ttl": "3600",
                                      "note": "E-Mail-Weiterleitung (ForwardEmail.net)", "category": "email"})
                seen_mx = True
            email_records.append({"type": "TXT", "name": "@",
                                  "value": f"forward-email={alias}:{ziel}", "ttl": "3600",
                                  "note": f"{alias}@{clean_domain} -> {ziel}", "category": "email"})

    return {
        "domain": clean_domain,
        "netlify_url": netlify_site_url,
        "records": records,
        "email_records": email_records,
        "instructions": (
            f"Bitte loggen Sie sich bei Ihrem Domain-Anbieter "
            f"(z.B. IONOS, Strato, united-domains, GoDaddy) ein und tragen Sie "
            f"die folgenden DNS-Eintraege fuer '{clean_domain}' ein. "
            f"Die Aenderungen werden innerhalb von 1-48 Stunden aktiv. "
            f"Wir informieren Sie automatisch, sobald Ihre Website live ist."
        ),
        "email_instructions": (
            "Fuer E-Mail-Weiterleitungen: Tragen Sie zusaetzlich die MX- und "
            "TXT-Eintraege ein. Eingehende E-Mails werden automatisch "
            "an Ihre bestehende E-Mail-Adresse weitergeleitet."
        ) if email_records else None,
    }


async def set_domain_alias(site_id: str, alias: str) -> dict:
    """Fuegt einen Domain-Alias zu einer Netlify-Site hinzu."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        get_resp = await client.get(f"{NETLIFY_API}/sites/{site_id}", headers=_get_headers())
        existing = get_resp.json().get("domain_aliases", []) if get_resp.is_success else []
        if alias not in existing:
            existing.append(alias)
        resp = await client.put(f"{NETLIFY_API}/sites/{site_id}", headers=_get_headers(),
                                json={"domain_aliases": existing})
    if not resp.is_success:
        raise Exception(f"Domain-Alias Fehler: {resp.status_code}")
    return {"aliases": resp.json().get("domain_aliases", [])}


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
