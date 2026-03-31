import httpx
import asyncio
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def check_domain(url: str) -> dict:
    """Prüft eine Domain auf Erreichbarkeit, Redirects und Parking."""
    if not url.startswith('http'):
        url = 'https://' + url

    result = {
        'original_url': url, 'final_url': url, 'reachable': False,
        'has_redirect': False, 'redirect_chain': [], 'redirect_count': 0,
        'is_https': url.startswith('https'), 'final_is_https': False,
        'status_code': None, 'error': None,
        'skip_import': False, 'skip_reason': '',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; KOMPAGNON-Audit/1.0)',
        'Accept': 'text/html', 'Accept-Language': 'de-DE,de;q=0.9',
    }

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, max_redirects=10, verify=False) as client:
            response = await client.get(url, headers=headers)

            history = response.history
            redirect_chain = [{'url': str(r.url), 'status_code': r.status_code} for r in history]
            final_url = str(response.url)

            result['final_url'] = final_url
            result['status_code'] = response.status_code
            result['reachable'] = response.status_code < 400
            result['has_redirect'] = len(history) > 0
            result['redirect_chain'] = redirect_chain
            result['redirect_count'] = len(history)
            result['final_is_https'] = final_url.startswith('https')

            final_domain = urlparse(final_url).netloc.replace('www.', '')
            original_domain = urlparse(url).netloc.replace('www.', '')

            if result['has_redirect'] and final_domain != original_domain:
                result['skip_import'] = True
                result['skip_reason'] = f'Redirect auf andere Domain: {final_domain}'
                logger.warning(f'Redirect auf andere Domain: {url} → {final_url}')

            parking_keywords = ['domain parking', 'this domain is for sale', 'buy this domain',
                                'domain expired', 'sedoparking', 'hugedomains', 'domain for sale']
            body_lower = response.text[:5000].lower()
            for kw in parking_keywords:
                if kw in body_lower:
                    result['skip_import'] = True
                    result['skip_reason'] = 'Parkierte Domain (kein echter Inhalt)'
                    break

            if result['has_redirect']:
                logger.info(f'Redirect: {url} → {final_url} ({len(history)} Schritte)')

    except httpx.ConnectError:
        result['error'] = 'Nicht erreichbar'
        result['skip_import'] = True
        result['skip_reason'] = 'Domain nicht erreichbar'
    except httpx.TimeoutException:
        result['error'] = 'Timeout'
        result['skip_import'] = True
        result['skip_reason'] = 'Timeout'
    except Exception as e:
        result['error'] = str(e)
        result['skip_import'] = True
        result['skip_reason'] = f'Fehler: {str(e)[:80]}'

    return result


async def check_domains_batch(urls: list, concurrency: int = 3) -> list:
    """Prüft mehrere Domains gleichzeitig (max 3 parallel)."""
    semaphore = asyncio.Semaphore(concurrency)

    async def check_with_limit(u):
        async with semaphore:
            return await check_domain(u)

    results = await asyncio.gather(*[check_with_limit(u) for u in urls], return_exceptions=True)

    output = []
    for u, r in zip(urls, results):
        if isinstance(r, Exception):
            output.append({'original_url': u, 'final_url': u, 'reachable': False, 'has_redirect': False,
                           'redirect_chain': [], 'skip_import': True, 'skip_reason': str(r), 'error': str(r),
                           'redirect_count': 0, 'final_is_https': False})
        else:
            output.append(r)
    return output
