"""
SSL-Helper fuer KOMPAGNON Crawler und Brand-Scraper.

Kunden-Websites (Altbestand) haben haeufig unvollstaendige SSL-Zertifikatsketten
(fehlende Intermediate-Zertifikate) — besonders bei aelteren Strato/IONOS/1&1-Hosting.

Strategie:
  1. Erster Versuch: SSL-Pruefung aktiv (sicher, Standard)
  2. Zweiter Versuch: SSL-Pruefung deaktiviert (nur fuer externe Kunden-URLs)
  3. SSL-Status wird als Metadatum zurueckgegeben — nie verschwiegen

Bietet zwei Varianten:
  - fetch_with_ssl_fallback(...)        sync, fuer CLI-Tests / einmalige Calls
  - fetch_with_ssl_fallback_async(...)  async, fuer FastAPI-Endpoints
"""

import httpx
import logging

logger = logging.getLogger(__name__)

# Timeout fuer externe Kunden-Websites
EXTERNAL_TIMEOUT = 15

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _is_ssl_error(exc: Exception) -> bool:
    """Erkennt SSL-bezogene Fehler in httpx ConnectError / generischen Exceptions."""
    msg = str(exc).upper()
    return (
        "CERTIFICATE_VERIFY_FAILED" in msg
        or "SSL" in msg
        or "CERTIFICATE" in msg
    )


def _empty_result(error: str) -> dict:
    return {
        "content": None,
        "ssl_ok": False,
        "ssl_error": error,
        "reachable": False,
        "status_code": None,
    }


def fetch_with_ssl_fallback(url: str, headers: dict = None) -> dict:
    """
    Sync-Variante: Ruft eine externe URL ab. Versucht zuerst mit SSL-Pruefung,
    faellt bei SSL-Fehler auf unsicheren Modus zurueck.

    Gibt zurueck:
        {
            "content":     str | None,   # HTML-Inhalt
            "ssl_ok":      bool,         # True = Zertifikat gueltig
            "ssl_error":   str | None,   # Fehlermeldung wenn SSL kaputt
            "reachable":   bool,         # False = Website komplett offline
            "status_code": int | None,
        }
    """
    headers = headers or DEFAULT_HEADERS

    # Versuch 1: Mit SSL-Pruefung
    try:
        resp = httpx.get(url, headers=headers, timeout=EXTERNAL_TIMEOUT, follow_redirects=True)
        return {
            "content":     resp.text,
            "ssl_ok":      True,
            "ssl_error":   None,
            "reachable":   True,
            "status_code": resp.status_code,
        }
    except httpx.ConnectError as e:
        if not _is_ssl_error(e):
            logger.error(f"Verbindungsfehler fuer {url}: {e}")
            return _empty_result(str(e))
        logger.warning(f"SSL-Pruefung fehlgeschlagen fuer {url}: {e} — starte Fallback")
    except Exception as e:
        if not _is_ssl_error(e):
            logger.error(f"Unerwarteter Fehler fuer {url}: {e}")
            return _empty_result(str(e))
        logger.warning(f"SSL-Pruefung fehlgeschlagen fuer {url}: {e} — starte Fallback")

    # Versuch 2: Ohne SSL-Pruefung (Fallback fuer kaputte Zertifikate)
    try:
        logger.info(f"SSL-Fallback aktiv fuer {url} — scrape ohne Zertifikatspruefung")
        resp = httpx.get(
            url,
            headers=headers,
            timeout=EXTERNAL_TIMEOUT,
            follow_redirects=True,
            verify=False,  # Nur fuer externe Kunden-Altwebsites
        )
        return {
            "content":     resp.text,
            "ssl_ok":      False,
            "ssl_error":   "Unvollstaendige Zertifikatskette (Intermediate fehlt)",
            "reachable":   True,
            "status_code": resp.status_code,
        }
    except Exception as e:
        logger.error(f"Auch SSL-Fallback fehlgeschlagen fuer {url}: {e}")
        return _empty_result(str(e))


async def fetch_with_ssl_fallback_async(url: str, headers: dict = None) -> dict:
    """
    Async-Variante mit identischer Semantik fuer FastAPI-Endpoints.
    Gibt dasselbe Dict-Schema zurueck wie fetch_with_ssl_fallback().
    """
    headers = headers or DEFAULT_HEADERS

    # Versuch 1: Mit SSL-Pruefung
    try:
        async with httpx.AsyncClient(timeout=EXTERNAL_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
        return {
            "content":     resp.text,
            "ssl_ok":      True,
            "ssl_error":   None,
            "reachable":   True,
            "status_code": resp.status_code,
        }
    except httpx.ConnectError as e:
        if not _is_ssl_error(e):
            logger.error(f"Verbindungsfehler fuer {url}: {e}")
            return _empty_result(str(e))
        logger.warning(f"SSL-Pruefung fehlgeschlagen fuer {url}: {e} — starte Fallback")
    except Exception as e:
        if not _is_ssl_error(e):
            logger.error(f"Unerwarteter Fehler fuer {url}: {e}")
            return _empty_result(str(e))
        logger.warning(f"SSL-Pruefung fehlgeschlagen fuer {url}: {e} — starte Fallback")

    # Versuch 2: Ohne SSL-Pruefung
    try:
        logger.info(f"SSL-Fallback (async) aktiv fuer {url}")
        async with httpx.AsyncClient(
            timeout=EXTERNAL_TIMEOUT,
            follow_redirects=True,
            verify=False,
        ) as client:
            resp = await client.get(url, headers=headers)
        return {
            "content":     resp.text,
            "ssl_ok":      False,
            "ssl_error":   "Unvollstaendige Zertifikatskette (Intermediate fehlt)",
            "reachable":   True,
            "status_code": resp.status_code,
        }
    except Exception as e:
        logger.error(f"Auch async SSL-Fallback fehlgeschlagen fuer {url}: {e}")
        return _empty_result(str(e))
