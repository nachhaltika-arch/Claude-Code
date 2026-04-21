"""
Hosting-Erkennung: IP-Lookup, WHOIS, DNS, WordPress-Hosting-Erkennung, Tech-Stack
"""
import asyncio
import re
import socket
from datetime import datetime
from typing import Optional

import dns.resolver
import httpx
import whois

WORDPRESS_HOSTING_PATTERNS = {
    "WP Engine":   ["wpengine.com", "wpenginepowered.com"],
    "Kinsta":      ["kinsta.cloud", "kinstacdn.com"],
    "Flywheel":    ["flywheelsites.com"],
    "SiteGround":  ["sgp.io", "siteground"],
    "Raidboxes":   ["raidboxes.io", "raidboxes.de"],
    "Cloudways":   ["cloudwaysapps.com"],
    "Pressidium":  ["pressidium.com"],
    "Pantheon":    ["pantheonsite.io"],
}

DNS_PROVIDER_PATTERNS = {
    "cloudflare": "Cloudflare",
    "google":     "Google DNS",
    "ionos":      "IONOS",
    "strato":     "Strato",
    "hetzner":    "Hetzner",
}

# ── Technologie-Erkennung ────────────────────────────────────────────────────

TECH_PATTERNS = [
    # CMS
    ("TYPO3",           ["typo3"]),
    ("Joomla",          ["joomla"]),
    ("Drupal",          ["drupal"]),
    ("Wix",             ["wixsite.com", "static.wixstatic.com", "wix.com"]),
    ("Squarespace",     ["squarespace.com", "squarespace-cdn.com"]),
    ("Webflow",         ["webflow.io", "webflow.com"]),
    ("Jimdo",           ["jimdo.com", "jimdosite.com"]),
    ("Shopware",        ["shopware"]),
    ("OXID",            ["oxid"]),
    ("Contao",          ["contao"]),
    # Page Builder
    ("Elementor",       ["elementor"]),
    ("Divi",            ["/et-", "divi-theme", "divi/"]),
    ("WP Bakery",       ["wpb_", "vc_row", "vc_column"]),
    # E-Commerce
    ("WooCommerce",     ["woocommerce"]),
    ("Shopify",         ["shopify.com", "cdn.shopify"]),
    ("Magento",         ["mage/", "magento"]),
    # CRM / Marketing
    ("HubSpot",         ["hubspot.com", "hs-scripts.com", "hs-analytics.net"]),
    ("Salesforce",      ["salesforce.com", "pardot.com", "force.com"]),
    ("Zoho CRM",        ["zoho.com"]),
    ("Pipedrive",       ["pipedrive.com"]),
    ("ActiveCampaign",  ["activecampaign.com"]),
    ("Mailchimp",       ["mailchimp.com", "chimpstatic.com"]),
    ("Brevo",           ["brevo.com", "sendinblue.com"]),
    ("Klaviyo",         ["klaviyo.com"]),
    # Booking
    ("Calendly",        ["calendly.com"]),
    ("SimplyBook",      ["simplybook.me"]),
    ("Bookingkit",      ["bookingkit.net"]),
    ("Eversports",      ["eversports.de"]),
    # Analytics
    ("Google Analytics",["gtag/js", "google-analytics.com", "googletagmanager.com"]),
    ("Matomo",          ["matomo.js", "piwik.js", "matomo.php"]),
    ("Hotjar",          ["hotjar.com"]),
    ("Microsoft Clarity",["clarity.ms"]),
    # Chat / Support
    ("Intercom",        ["intercom.io", "widget.intercom.io"]),
    ("LiveChat",        ["livechatinc.com"]),
    ("Tidio",           ["tidiochat.com", "tidio.co"]),
    ("Zendesk",         ["zopim.com", "zendesk.com"]),
    ("Freshdesk",       ["freshdesk.com", "freshchat.com"]),
]


def detect_technologies(html: str, headers: dict) -> list[str]:
    """Erkennt eingesetzte Technologien anhand von HTML-Inhalt und HTTP-Headern."""
    combined = (html[:80_000] + " " + " ".join(headers.values())).lower()
    detected = []
    for name, patterns in TECH_PATTERNS:
        if any(p.lower() in combined for p in patterns):
            detected.append(name)
    return detected


def extract_domain(website_url: str) -> str:
    """Entfernt http/https/www und gibt die reine Domain zurück."""
    domain = re.sub(r"^https?://", "", website_url.strip())
    domain = re.sub(r"^www\.", "", domain)
    domain = domain.split("/")[0].split("?")[0].split("#")[0]
    return domain.lower()


async def get_ip_and_hosting(domain: str) -> dict:
    try:
        ip_address = socket.gethostbyname(domain)
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"https://ipinfo.io/{ip_address}/json")
            data = r.json() if r.status_code == 200 else {}

        org = data.get("org", "")
        # Entferne führende AS-Nummer z.B. "AS24940 " → "Hetzner Online GmbH"
        hosting_provider = re.sub(r"^AS\d+\s+", "", org).strip() or None

        return {
            "ip_address": ip_address,
            "hosting_provider": hosting_provider,
            "hosting_org": org or None,
            "country": data.get("country") or None,
            "city": data.get("city") or None,
        }
    except Exception:
        return {}


def get_nameservers(domain: str) -> dict:
    try:
        answers = dns.resolver.resolve(domain, "NS")
        nameservers = [str(r).rstrip(".").lower() for r in answers]

        dns_provider = None
        for ns in nameservers:
            for pattern, name in DNS_PROVIDER_PATTERNS.items():
                if pattern in ns:
                    dns_provider = name
                    break
            if dns_provider:
                break

        return {"nameservers": nameservers, "dns_provider": dns_provider}
    except Exception:
        return {"nameservers": [], "dns_provider": None}


def get_whois_info(domain: str) -> dict:
    try:
        w = whois.whois(domain)

        def _fmt(d) -> Optional[str]:
            if d is None:
                return None
            if isinstance(d, list):
                d = d[0]
            return str(d)[:10]

        return {
            "registrar": w.registrar or None,
            "domain_created": _fmt(w.creation_date),
            "domain_expires": _fmt(w.expiration_date),
            "domain_updated": _fmt(w.updated_date),
        }
    except Exception:
        return {}


async def check_wordpress_hosting(website_url: str) -> dict:
    try:
        async with httpx.AsyncClient(
            timeout=8,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; KompagnonBot/1.0)"},
        ) as client:
            r = await client.get(website_url)

        headers = {k.lower(): v for k, v in r.headers.items()}
        html = r.text[:50_000]  # Nur erste 50 KB prüfen

        server_software = headers.get("server") or None
        powered_by = headers.get("x-powered-by") or None
        cdn_info = headers.get("via") or headers.get("x-cache") or None

        # WordPress-Hosting anhand URL/Header erkennen
        wordpress_hosting = None
        combined = " ".join([
            r.url.host,
            server_software or "",
            powered_by or "",
            cdn_info or "",
        ]).lower()

        for provider, patterns in WORDPRESS_HOSTING_PATTERNS.items():
            if any(p in combined for p in patterns):
                wordpress_hosting = provider
                break

        # WordPress generell erkennen
        is_wordpress = (
            "wp-content" in html
            or "wp-includes" in html
            or "wordpress" in (powered_by or "").lower()
            or "wordpress" in html[:5000].lower()
        )

        technologies = detect_technologies(html, headers)

        return {
            "server_software": server_software,
            "powered_by": powered_by,
            "cdn_info": cdn_info,
            "wordpress_hosting": wordpress_hosting,
            "is_wordpress": is_wordpress,
            "detected_technologies": technologies,
        }
    except Exception:
        return {}


async def scrape_hosting_info(website_url: str) -> dict:
    """Orchestriert alle Hosting-Abfragen parallel und merged die Ergebnisse."""
    domain = extract_domain(website_url)

    loop = asyncio.get_event_loop()

    ip_task = get_ip_and_hosting(domain)
    ns_task = loop.run_in_executor(None, get_nameservers, domain)
    whois_task = loop.run_in_executor(None, get_whois_info, domain)
    wp_task = check_wordpress_hosting(website_url)

    results = await asyncio.gather(ip_task, ns_task, whois_task, wp_task, return_exceptions=True)

    merged: dict = {
        "domain": domain,
        "website_url": website_url,
        "checked_at": datetime.utcnow().isoformat(),
    }

    for r in results:
        if isinstance(r, dict):
            merged.update(r)

    return merged
