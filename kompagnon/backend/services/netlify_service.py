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


def _get_headers(token: str = None) -> dict:
    """Load token at call-time; raises ValueError if missing so callers get HTTP 400/502."""
    t = (token or os.getenv("NETLIFY_API_TOKEN", "")).strip()
    if not t:
        raise ValueError(
            "NETLIFY_API_TOKEN ist nicht gesetzt. "
            "Bitte in Render.com unter Environment → Add Environment Variable eintragen."
        )
    return {
        "Authorization": f"Bearer {t}",
        "Content-Type":  "application/json",
    }


def _build_full_html(
    page_name: str,
    html: str,
    css: str = "",
    shared_css: str = "",
    meta_description: str = "",
    company_name: str = "",
) -> str:
    """
    Builds a complete HTML document from a GrapesJS body fragment.
    GrapesJS exports only body content — this adds DOCTYPE, head, charset,
    viewport, title, meta description, OG tags and embedded CSS.
    shared_css is prepended; page-specific css follows.
    """
    title = (
        f"{page_name} — {company_name}" if page_name and company_name
        else page_name or company_name or "Website"
    )
    og_desc = meta_description or (
        f"Offizielle Website von {company_name}" if company_name else title
    )

    combined_css = "\n".join(filter(None, [shared_css.strip(), css.strip()]))
    style_block = f"<style>\n{combined_css}\n</style>" if combined_css else ""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{og_desc}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:type" content="website">
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
        full_html = _build_full_html(
            page_name=page_title,
            html=html,
            css=css,
            meta_description=meta_description,
            company_name=company_name,
        )
        zf.writestr("index.html", full_html)
        zf.writestr(
            "_redirects",
            redirects if redirects else "/*  /index.html  200",
        )
        zf.writestr("_headers", default_headers)
    zip_bytes = buf.getvalue()

    t = os.getenv("NETLIFY_API_TOKEN", "").strip()
    if not t:
        raise ValueError("NETLIFY_API_TOKEN fehlt")
    deploy_headers = {
        "Authorization": f"Bearer {t}",
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
    shared_css: optional — shared CSS embedded before per-page CSS in every page
    company_name: Fallback fuer Meta-Tags

    Rueckgabe: { deploy_id, deploy_url, state }
    """
    default_headers = (
        "/*\n"
        "  X-Frame-Options: DENY\n"
        "  X-Content-Type-Options: nosniff"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        for filename, page in page_files.items():
            full_html = _build_full_html(
                page_name=page.get("page_title") or company_name,
                html=page.get("html", ""),
                css=page.get("css", ""),
                shared_css=shared_css,
                meta_description=page.get("meta_desc", ""),
                company_name=company_name,
            )
            zf.writestr(filename, full_html)

        # Keine SPA-Redirect-Regel — echte Dateien fuer echte Pfade
        zf.writestr("_redirects", "")
        zf.writestr("_headers", default_headers)

    zip_bytes = buf.getvalue()

    t = os.getenv("NETLIFY_API_TOKEN", "").strip()
    if not t:
        raise ValueError("NETLIFY_API_TOKEN fehlt")
    deploy_headers = {
        "Authorization": f"Bearer {t}",
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
    """
    Prüft ob die Domain bereits auf Netlify zeigt.

    Methode 1: IP-Präfix-Prüfung gegen bekannte Netlify Load-Balancer Ranges
    Methode 2: IP-Vergleich mit der tatsächlichen Netlify-Site-IP (falls URL bekannt)
    Methode 3: CNAME-Record-Prüfung via nslookup (prüft ob auf *.netlify.app zeigt)
    """
    import socket
    import subprocess

    clean = (domain or "").lower().strip()
    if not clean:
        return False

    netlify_host = (netlify_site_url or "").replace("https://", "").replace("http://", "").rstrip("/")

    hosts_to_check = [clean]
    if not clean.startswith("www."):
        hosts_to_check.append(f"www.{clean}")

    # Bekannte Netlify Load-Balancer IP-Ranges (Stand 2024)
    netlify_ip_prefixes = ("75.2.", "99.83.", "3.33.", "35.71.")

    for host in hosts_to_check:
        # Methode 1 + 2: IP auflösen
        try:
            ip = socket.gethostbyname(host)
            if any(ip.startswith(prefix) for prefix in netlify_ip_prefixes):
                return True
            # Methode 2: IP mit tatsächlicher Netlify-Site vergleichen
            if netlify_host:
                try:
                    netlify_ip = socket.gethostbyname(netlify_host)
                    if ip == netlify_ip:
                        return True
                except Exception:
                    pass
        except Exception:
            pass

        # Methode 3: CNAME via nslookup prüfen
        try:
            result = subprocess.run(
                ["nslookup", "-type=CNAME", host],
                capture_output=True, text=True, timeout=5,
            )
            output = result.stdout.lower()
            if "netlify.app" in output or (netlify_host and netlify_host.lower() in output):
                return True
        except Exception:
            pass

    return False


def generate_dns_guide(domain: str, netlify_site_url: str,
                       email_forwarding: list | None = None) -> dict:
    """
    Erzeugt DNS-Einträge + optionale E-Mail-Weiterleitungen.

    email_forwarding: Liste von {alias: 'info', ziel: 'chef@gmail.com'}
    """
    clean_domain = (domain or "").lower().strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]
    clean_domain = clean_domain.lstrip(".")

    netlify_host = (netlify_site_url or "").replace("https://", "").replace("http://", "").rstrip("/")
    if not netlify_host:
        netlify_host = "<ihre-netlify-subdomain>.netlify.app"

    records = [
        {
            "type":  "A",
            "name":  "@",
            "value": "75.2.60.5",
            "ttl":   "3600",
            "note":  "Hauptdomain (ohne www)",
            "category": "website",
        },
        {
            "type":  "CNAME",
            "name":  "www",
            "value": netlify_host,
            "ttl":   "3600",
            "note":  "www-Subdomain",
            "category": "website",
        },
    ]

    email_records = []
    if email_forwarding:
        for fwd in email_forwarding:
            alias = fwd.get("alias", "info")
            ziel  = fwd.get("ziel", "")
            if ziel:
                email_records.append({
                    "type":     "MX",
                    "name":     "@",
                    "value":    "mx1.forwardemail.net",
                    "priority": "10",
                    "ttl":      "3600",
                    "note":     "E-Mail-Weiterleitung (ForwardEmail.net — kostenlos)",
                    "category": "email",
                })
                email_records.append({
                    "type":     "TXT",
                    "name":     "@",
                    "value":    f"forward-email={alias}:{ziel}",
                    "ttl":      "3600",
                    "note":     f"{alias}@{clean_domain} → {ziel}",
                    "category": "email",
                })

    return {
        "domain":        clean_domain,
        "netlify_url":   netlify_site_url,
        "records":       records,
        "email_records": email_records,
        "email_service": "ForwardEmail.net (DSGVO-konform, kostenlos für Weiterleitungen)",
        "instructions":  (
            f"Bitte loggen Sie sich bei Ihrem Domain-Anbieter ein "
            f"(z.B. IONOS, Strato, united-domains, GoDaddy) und tragen Sie "
            f"die folgenden DNS-Einträge für '{clean_domain}' ein. "
            f"Die Änderungen werden innerhalb von 1–48 Stunden aktiv."
        ),
        "email_instructions": (
            "Für E-Mail-Weiterleitungen: Tragen Sie zusätzlich die MX- und "
            "TXT-Einträge ein. Eingehende E-Mails werden dann automatisch "
            "an Ihre bestehende E-Mail-Adresse weitergeleitet — "
            "Sie benötigen keinen eigenen Mailserver."
        ) if email_records else None,
    }


async def set_domain_alias(site_id: str, alias: str) -> dict:
    """Fügt einen Domain-Alias zu einer Netlify-Site hinzu."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        get_resp = await client.get(
            f"{NETLIFY_API}/sites/{site_id}",
            headers=_get_headers(),
        )
        existing = get_resp.json().get("domain_aliases", []) if get_resp.is_success else []

        if alias not in existing:
            existing.append(alias)

        resp = await client.put(
            f"{NETLIFY_API}/sites/{site_id}",
            headers=_get_headers(),
            json={"domain_aliases": existing},
        )

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
