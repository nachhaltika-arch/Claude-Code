"""
Erheber für das Website-Audit — liefert Fakten, keine Punkte.

Jede Funktion gibt entweder ein Ergebnis mit ``"collected": True`` zurück oder
``{"collected": False, "reason": ...}``. Die Bewertung passiert ausschließlich in
``audit_scoring``; hier wird nichts geschätzt und nichts geraten.

Vorher wurden diese Werte im Audit als Konstanten vergeben (Bildoptimierung 1,
Drittanbieter 2, Formularsicherheit 1 …) — unabhängig von der geprüften Seite.
"""
import asyncio
import logging
import re
import socket
import ssl
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from services.url_guard import assert_safe_url, is_same_host

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

HTTP_TIMEOUT = 8.0
SUBPAGE_TIMEOUT = 6.0
MAX_IMAGES_SAMPLED = 8
IMAGE_SIZE_WARN_KB = 300

# Bekannte Consent-Management-Tools. Das bloße Vorkommen des Wortes "Cookie"
# reichte bisher für die volle Punktzahl — das trifft praktisch jede Seite.
CMP_SIGNATURES = (
    "cookiebot", "usercentrics", "borlabs", "onetrust", "cookieyes",
    "complianz", "klaro", "consentmanager", "iubenda", "termly",
    "real cookie banner", "ccm19", "sourcepoint", "didomi", "osano",
    "cookiefirst", "cookie-script", "cookieconsent", "tarteaucitron",
)

# Dienste, die ohne vorherige Einwilligung nicht geladen werden dürfen.
THIRD_PARTY_SIGNATURES = {
    "google_fonts": ("fonts.googleapis.com", "fonts.gstatic.com"),
    "google_maps": ("maps.google", "maps.googleapis", "maps.gstatic", "google.com/maps/embed"),
    "google_analytics": ("google-analytics.com", "googletagmanager.com", "gtag/js"),
    "facebook": ("connect.facebook.net", "facebook.com/tr"),
    "youtube": ("youtube.com/embed",),
    "doubleclick": ("doubleclick.net",),
    "hotjar": ("hotjar.com",),
    "clarity": ("clarity.ms",),
}

CDN_HEADER_SIGNATURES = {
    "cf-ray": "Cloudflare",
    "x-amz-cf-id": "AWS CloudFront",
    "x-fastly-request-id": "Fastly",
    "x-akamai-transformed": "Akamai",
    "x-served-by": "Varnish/Fastly",
    "x-vercel-id": "Vercel",
    "x-nf-request-id": "Netlify",
}

IMPRESSUM_PATTERNS = ("impressum", "imprint", "anbieterkennzeichnung")
DATENSCHUTZ_PATTERNS = ("datenschutz", "privacy", "datenschutzerklaerung")
BFSG_PATTERNS = ("barrierefreiheit", "accessibility", "barrierefreiheitserklärung")

MODERN_IMAGE_FORMATS = (".webp", ".avif")
LEGACY_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")


# ═══════════════════════════════════════════════════════════════════
# TLS
# ═══════════════════════════════════════════════════════════════════

def check_tls(url: str) -> dict:
    """Echter TLS-Handshake mit Zertifikatsprüfung.

    Der Altcode vergab die volle Punktzahl, sobald die URL mit 'https://' begann,
    und lud die Seite zusätzlich mit ``verify=False``. Ein abgelaufenes oder auf
    eine fremde Domain ausgestelltes Zertifikat fiel damit nirgends auf.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return {
            "collected": True, "valid": False, "reason": "kein_https",
            "uses_https": False,
        }

    host = parsed.hostname or ""
    port = parsed.port or 443

    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=6) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
                protocol = tls.version()

        not_after = cert.get("notAfter")
        expires_at = None
        days_left = None
        if not_after:
            expires_at = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            days_left = (expires_at - datetime.now(timezone.utc)).days

        issuer = ""
        for part in cert.get("issuer", ()):
            for name, value in part:
                if name == "organizationName":
                    issuer = value

        return {
            "collected": True,
            "valid": True,
            "uses_https": True,
            "hostname_match": True,   # wrap_socket prüft den Hostnamen bereits
            "expires_at": expires_at.isoformat() if expires_at else None,
            "days_left": days_left,
            "expires_soon": days_left is not None and days_left < 30,
            "issuer": issuer,
            "protocol": protocol,
        }

    except ssl.SSLCertVerificationError as e:
        return {"collected": True, "valid": False, "uses_https": True,
                "reason": "zertifikat_ungueltig", "detail": str(e)[:200]}
    except (socket.timeout, socket.gaierror, ConnectionError, OSError) as e:
        return {"collected": True, "valid": False, "uses_https": True,
                "reason": "handshake_fehlgeschlagen", "detail": str(e)[:200]}
    except Exception as e:  # noqa: BLE001 — Erhebung darf das Audit nie abbrechen
        logger.warning(f"TLS-Prüfung fehlgeschlagen für {url}: {e}")
        return {"collected": False, "reason": f"{type(e).__name__}: {e}"[:200]}


async def check_https_redirect(url: str) -> dict:
    """Prüft, ob die http-Variante zwingend auf https weiterleitet."""
    parsed = urlparse(url)
    http_url = f"http://{parsed.netloc}{parsed.path or '/'}"
    try:
        assert_safe_url(http_url)
        async with httpx.AsyncClient(timeout=SUBPAGE_TIMEOUT, follow_redirects=False) as c:
            r = await c.get(http_url, headers={"User-Agent": USER_AGENT})
        location = r.headers.get("location", "")
        return {
            "collected": True,
            "redirects": r.status_code in (301, 302, 307, 308) and location.startswith("https"),
            "status_code": r.status_code,
            "location": location[:200],
        }
    except Exception as e:  # noqa: BLE001
        return {"collected": False, "reason": f"{type(e).__name__}: {e}"[:200]}


# ═══════════════════════════════════════════════════════════════════
# Rechtsseiten
# ═══════════════════════════════════════════════════════════════════

def _find_link(soup: BeautifulSoup, base_url: str, patterns) -> Optional[str]:
    """Findet einen Link — nur auf derselben Domain.

    Ohne die Host-Prüfung könnte ein Link im fremden HTML den serverseitigen
    Abruf auf ein internes Ziel lenken.
    """
    for a in soup.find_all("a", href=True):
        haystack = f"{a['href']} {a.get_text()}".lower()
        if any(p in haystack for p in patterns):
            candidate = urljoin(base_url, a["href"])
            if is_same_host(candidate, base_url):
                return candidate
    return None


async def _fetch(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        r = await client.get(url, headers={"User-Agent": USER_AGENT})
        return r.text if r.status_code == 200 else None
    except Exception:  # noqa: BLE001
        return None


async def check_legal_pages(base_url: str, soup: BeautifulSoup) -> dict:
    """Lädt Impressum und Datenschutzerklärung und prüft ihre Pflichtinhalte.

    Bisher galt ein Impressum als vorhanden, sobald das Wort irgendwo im
    Startseiten-HTML stand — ob die Seite existiert, wurde nie geprüft.
    """
    impressum_url = _find_link(soup, base_url, IMPRESSUM_PATTERNS)
    datenschutz_url = _find_link(soup, base_url, DATENSCHUTZ_PATTERNS)
    bfsg_url = _find_link(soup, base_url, BFSG_PATTERNS)

    result: Dict[str, object] = {"collected": True}

    async with httpx.AsyncClient(timeout=SUBPAGE_TIMEOUT, follow_redirects=True) as client:
        impressum_html, datenschutz_html = await asyncio.gather(
            _fetch(client, impressum_url) if impressum_url else _none(),
            _fetch(client, datenschutz_url) if datenschutz_url else _none(),
        )

    result["impressum"] = _evaluate_impressum(impressum_url, impressum_html)
    result["datenschutz"] = _evaluate_datenschutz(datenschutz_url, datenschutz_html)
    result["bfsg"] = {"url": bfsg_url, "linked": bool(bfsg_url)}
    return result


async def _none():
    return None


def _evaluate_impressum(url: Optional[str], html: Optional[str]) -> dict:
    if not url or not html:
        return {"url": url, "reachable": False, "fields": {}, "complete": False}

    text = BeautifulSoup(html, "html.parser").get_text(" ").lower()
    fields = {
        "anschrift": bool(re.search(r"\b\d{5}\s+[a-zäöüß]", text)),
        "kontakt": ("telefon" in text or "tel." in text or "@" in text),
        "vertretung": any(k in text for k in
                          ("vertreten durch", "geschäftsführer", "inhaber", "vorstand")),
        "register": any(k in text for k in
                        ("ust-id", "umsatzsteuer", "hrb", "handelsregister", "steuernummer")),
        "kammer": any(k in text for k in
                      ("handwerkskammer", "kammer", "ihk", "berufsbezeichnung")),
    }
    core = ("anschrift", "kontakt", "vertretung", "register")
    return {
        "url": url,
        "reachable": True,
        "fields": fields,
        "complete": all(fields[k] for k in core),
        "missing": [k for k in core if not fields[k]],
    }


def _evaluate_datenschutz(url: Optional[str], html: Optional[str]) -> dict:
    if not url or not html:
        return {"url": url, "reachable": False, "fields": {}, "complete": False}

    text = BeautifulSoup(html, "html.parser").get_text(" ").lower()
    fields = {
        "verantwortlicher": "verantwortlich" in text,
        "rechtsgrundlage": ("art. 6" in text or "artikel 6" in text or "rechtsgrundlage" in text),
        "betroffenenrechte": any(k in text for k in
                                 ("auskunft", "löschung", "widerspruch", "betroffenenrechte")),
        "aufsichtsbehoerde": ("aufsichtsbehörde" in text or "beschwerde" in text),
        "speicherdauer": ("speicherdauer" in text or "speicherfrist" in text),
    }
    core = ("verantwortlicher", "rechtsgrundlage", "betroffenenrechte")
    return {
        "url": url,
        "reachable": True,
        "fields": fields,
        "complete": all(fields[k] for k in core),
        "missing": [k for k in core if not fields[k]],
    }


# ═══════════════════════════════════════════════════════════════════
# Consent und Drittanbieter
# ═══════════════════════════════════════════════════════════════════

def detect_consent(html: str) -> dict:
    """Erkennt ein echtes Consent-Tool statt nur das Wort 'Cookie'."""
    lower = html.lower()
    found = [name for name in CMP_SIGNATURES if name in lower]
    return {
        "collected": True,
        "cmp_detected": bool(found),
        "cmp_names": found,
        "mentions_cookie_only": bool(not found and "cookie" in lower),
    }


def detect_third_parties(html: str) -> dict:
    """Externe Dienste, die vor einer Einwilligung nicht geladen werden dürfen."""
    lower = html.lower()
    found = {
        name: True
        for name, signatures in THIRD_PARTY_SIGNATURES.items()
        if any(s in lower for s in signatures)
    }
    tracking = [n for n in found if n in ("google_analytics", "facebook", "doubleclick",
                                          "hotjar", "clarity")]
    return {
        "collected": True,
        "services": sorted(found),
        "tracking_services": sorted(tracking),
        "external_fonts": "google_fonts" in found,
        "maps_embedded": "google_maps" in found,
        "count": len(found),
    }


def detect_cdn(headers: Dict[str, str]) -> dict:
    lower = {k.lower(): v for k, v in headers.items()}
    for header, provider in CDN_HEADER_SIGNATURES.items():
        if header in lower:
            return {"collected": True, "cdn_active": True, "provider": provider}
    via = lower.get("via", "").lower()
    if any(s in via for s in ("cloudfront", "varnish", "cloudflare")):
        return {"collected": True, "cdn_active": True, "provider": via[:60]}
    return {"collected": True, "cdn_active": False, "provider": None}


# ═══════════════════════════════════════════════════════════════════
# Bilder und Formulare
# ═══════════════════════════════════════════════════════════════════

async def analyse_images(soup: BeautifulSoup, base_url: str) -> dict:
    """Format, Lazy Loading, feste Dimensionen und Dateigröße einer Stichprobe."""
    images = soup.find_all("img")
    if not images:
        return {"collected": True, "total": 0, "note": "keine Bilder gefunden"}

    modern = legacy = lazy = with_dimensions = 0
    sources: List[str] = []

    for img in images:
        src = (img.get("src") or img.get("data-src") or "").lower()
        if any(src.endswith(ext) or f"{ext}?" in src for ext in MODERN_IMAGE_FORMATS):
            modern += 1
        elif any(src.endswith(ext) or f"{ext}?" in src for ext in LEGACY_IMAGE_FORMATS):
            legacy += 1
        if img.get("loading") == "lazy":
            lazy += 1
        if img.get("width") and img.get("height"):
            with_dimensions += 1
        if src and not src.startswith("data:"):
            absolute = urljoin(base_url, img.get("src") or img.get("data-src"))
            if is_same_host(absolute, base_url):
                sources.append(absolute)

    oversized = await _sample_image_sizes(sources[:MAX_IMAGES_SAMPLED])
    total = len(images)

    return {
        "collected": True,
        "total": total,
        "modern_format": modern,
        "legacy_format": legacy,
        "modern_share": round(modern / total * 100) if total else 0,
        "lazy_loading": lazy,
        "lazy_share": round(lazy / total * 100) if total else 0,
        "with_dimensions": with_dimensions,
        "dimension_share": round(with_dimensions / total * 100) if total else 0,
        "sampled": len(sources[:MAX_IMAGES_SAMPLED]),
        "oversized": oversized,
    }


async def _sample_image_sizes(urls: List[str]) -> int:
    """Zählt Bilder über der Größenschwelle in einer Stichprobe."""
    if not urls:
        return 0

    async def _size(client: httpx.AsyncClient, url: str) -> int:
        try:
            r = await client.head(url, headers={"User-Agent": USER_AGENT})
            return int(r.headers.get("content-length", 0))
        except Exception:  # noqa: BLE001
            return 0

    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            sizes = await asyncio.gather(*[_size(client, u) for u in urls])
        return sum(1 for s in sizes if s > IMAGE_SIZE_WARN_KB * 1024)
    except Exception:  # noqa: BLE001
        return 0


def analyse_forms(soup: BeautifulSoup, base_url: str) -> dict:
    """Formularsicherheit: HTTPS-Ziel, Methode, Einwilligungs-Checkbox."""
    forms = soup.find_all("form")
    if not forms:
        return {"collected": True, "total": 0}

    secure_action = post_method = with_consent = 0
    for form in forms:
        action = urljoin(base_url, form.get("action") or base_url)
        if action.startswith("https://"):
            secure_action += 1
        if (form.get("method") or "get").lower() == "post":
            post_method += 1

        checkboxes = form.find_all("input", attrs={"type": "checkbox"})
        context = " ".join(str(cb.parent) for cb in checkboxes if cb.parent).lower()
        if any(k in context for k in ("datenschutz", "privacy", "einverstanden", "akzeptier")):
            with_consent += 1

    return {
        "collected": True,
        "total": len(forms),
        "secure_action": secure_action,
        "post_method": post_method,
        "with_consent": with_consent,
        "all_secure": secure_action == len(forms),
        "all_consent": with_consent == len(forms),
    }


def analyse_navigation(soup: BeautifulSoup) -> dict:
    nav = soup.find_all("nav")
    nav_links = [a for n in nav for a in n.find_all("a", href=True)]
    return {
        "collected": True,
        "has_nav_element": bool(nav),
        "nav_link_count": len(nav_links),
        "total_links": len(soup.find_all("a", href=True)),
    }


RESPONSE_TIME_PATTERNS = (
    "innerhalb von", "rückruf", "melden uns", "antwort innerhalb",
    "24 stunden", "48 stunden", "werktag", "am selben tag", "sofort",
)

TRUST_PATTERNS = {
    "bewertungen": ("google bewertung", "sterne", "★", "rezension", "kundenstimmen",
                    "trustpilot", "provenexpert", "erfahrungen"),
    "referenzen": ("referenz", "projekte", "kundenprojekte", "unsere arbeiten",
                   "vorher", "nachher"),
    "zertifikate": ("meisterbetrieb", "innung", "handwerkskammer", "zertifiziert",
                    "tüv", "iso 9001", "fachbetrieb", "sachkundenachweis"),
    "team": ("unser team", "über uns", "mitarbeiter", "ansprechpartner", "geschäftsführer"),
    "garantie": ("garantie", "gewährleistung", "festpreis", "zufriedenheit"),
}

SERVICE_PAGE_PATTERNS = (
    "leistung", "service", "angebot", "wärmepumpe", "waermepumpe", "wallbox",
    "heizung", "sanitär", "sanitaer", "bad", "elektro", "photovoltaik",
    "solar", "klima", "lüftung", "notdienst", "wartung",
)

CURRENT_YEAR_WINDOW = 2  # Copyright älter als zwei Jahre gilt als veraltet


def analyse_contact(soup: BeautifulSoup) -> dict:
    """Kontaktwege und Hürden im Kontaktformular."""
    forms = soup.find_all("form")
    field_counts = [
        len(f.find_all(["input", "textarea", "select"]))
        for f in forms
    ]
    smallest_form = min(field_counts) if field_counts else None
    text = soup.get_text(" ").lower()

    return {
        "collected": True,
        "tel_link": bool(soup.find("a", href=lambda h: h and h.startswith("tel:"))),
        "mailto_link": bool(soup.find("a", href=lambda h: h and h.startswith("mailto:"))),
        "form": bool(forms),
        "form_field_count": smallest_form,
        "form_is_lean": smallest_form is not None and smallest_form <= 5,
        "response_time_stated": any(p in text for p in RESPONSE_TIME_PATTERNS),
    }


def analyse_trust(soup: BeautifulSoup) -> dict:
    """Vertrauenssignale — Bewertungen, Referenzen, Zertifikate, Team, Garantie."""
    text = soup.get_text(" ").lower()
    found = {
        name: any(p in text for p in patterns)
        for name, patterns in TRUST_PATTERNS.items()
    }
    return {
        "collected": True,
        **found,
        "signal_count": sum(1 for v in found.values() if v),
    }


def analyse_service_pages(soup: BeautifulSoup, base_url: str) -> dict:
    """Zählt eigenständige Leistungsseiten in der Navigation.

    Eine einzelne Sammelseite 'Leistungen' rankt deutlich schlechter als je
    eine Seite pro Gewerk — deshalb wird die Anzahl separat bewertet.
    """
    host = urlparse(base_url).netloc
    pages = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute = urljoin(base_url, href)
        if urlparse(absolute).netloc != host:
            continue
        haystack = f"{href} {a.get_text(' ')}".lower()
        if any(p in haystack for p in SERVICE_PAGE_PATTERNS):
            path = urlparse(absolute).path.rstrip("/").lower()
            if path and path != "/":
                pages.add(path)

    return {
        "collected": True,
        "service_page_count": len(pages),
        "pages": sorted(pages)[:12],
    }


def analyse_freshness(html: str, current_year: int) -> dict:
    """Aktualitätssignale: Copyright-Jahr und datierte Inhalte."""
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})",
                                        html, re.IGNORECASE)]
    newest = max(years) if years else None
    text_lower = html.lower()

    return {
        "collected": True,
        "copyright_year": newest,
        "copyright_current": newest is not None and newest >= current_year - CURRENT_YEAR_WINDOW,
        "has_dated_content": bool(re.search(r"\b\d{1,2}\.\s*\d{1,2}\.\s*20\d{2}\b", html)),
        "mentions_update": any(k in text_lower for k in ("aktualisiert", "stand:", "zuletzt")),
    }


CTA_KEYWORDS = (
    "termin", "angebot", "anfrage", "beratung", "kontakt", "rückruf",
    "jetzt", "kostenlos", "unverbindlich", "anfordern", "vereinbaren",
)


def analyse_cta(soup: BeautifulSoup) -> dict:
    """Sucht handlungsauffordernde Links und Buttons."""
    candidates = soup.find_all(["a", "button"])
    matches = [
        el.get_text(" ").strip()[:80]
        for el in candidates
        if any(k in el.get_text(" ").lower() for k in CTA_KEYWORDS)
    ]
    return {
        "collected": True,
        "cta_count": len(matches),
        "examples": matches[:5],
        "has_cta": bool(matches),
    }


def detect_shop(html: str) -> dict:
    """E-Commerce-Pflichten gelten nur, wenn es tatsächlich einen Shop gibt."""
    lower = html.lower()
    signals = ("woocommerce", "shopify", "shopware", "magento", "warenkorb",
               "add-to-cart", "zum warenkorb", "jetzt kaufen", "checkout")
    found = [s for s in signals if s in lower]
    return {"collected": True, "is_shop": bool(found), "signals": found}
