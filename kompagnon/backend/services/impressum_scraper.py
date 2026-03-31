import httpx
import re
import json
import os
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

IMPRESSUM_PATHS = [
    '/impressum',
    '/impressum.html',
    '/impressum/',
    '/imprint',
    '/legal',
    '/rechtliches',
    '/kontakt',
    '/about',
    '/ueber-uns',
]


async def fetch_impressum_text(website_url: str) -> str:
    """Versucht das Impressum der Website zu laden und gibt den Text zurück."""
    if not website_url.startswith('http'):
        website_url = 'https://' + website_url

    base = website_url.rstrip('/')

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; KOMPAGNON-Audit/1.0)',
        'Accept': 'text/html',
        'Accept-Language': 'de-DE,de;q=0.9',
    }

    found_text = ''

    async with httpx.AsyncClient(timeout=10, follow_redirects=True, verify=False) as client:
        # 1. Startseite laden um Impressum-Link zu finden
        try:
            res = await client.get(base, headers=headers)
            html = res.text

            links = re.findall(r'href=["\']([^"\']*?)["\']', html, re.IGNORECASE)
            impressum_link = None
            for link in links:
                if any(p in link.lower() for p in ['impressum', 'imprint', 'legal', 'rechtlich']):
                    impressum_link = link
                    break

            if impressum_link:
                if impressum_link.startswith('/'):
                    impressum_link = base + impressum_link
                elif not impressum_link.startswith('http'):
                    impressum_link = base + '/' + impressum_link

                try:
                    r2 = await client.get(impressum_link, headers=headers)
                    found_text = clean_html(r2.text)
                    if len(found_text) > 100:
                        return found_text[:8000]
                except:
                    pass
        except:
            pass

        # 2. Bekannte Pfade durchprobieren
        for path in IMPRESSUM_PATHS:
            try:
                url = base + path
                r = await client.get(url, headers=headers)
                if r.status_code == 200:
                    text = clean_html(r.text)
                    if len(text) > 200:
                        found_text = text
                        break
            except:
                continue

    return found_text[:8000] if found_text else ''


def clean_html(html: str) -> str:
    """HTML Tags entfernen und Text säubern."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&amp;', '&')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&#8203;', '')
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()


async def extract_contact_from_impressum(website_url: str) -> dict:
    """Lädt das Impressum und extrahiert Kontaktdaten mit KI."""
    impressum_text = await fetch_impressum_text(website_url)

    if not impressum_text:
        return {
            'success': False,
            'error': 'Impressum konnte nicht geladen werden. Bitte URL prüfen.',
        }

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        prompt = f"""Extrahiere alle Kontaktdaten aus diesem Impressum-Text.

Impressum-Text:
{impressum_text}

Gib NUR ein JSON-Objekt zurück — keine Erklärung, kein Markdown:
{{
  "company_name": "Firmenname ohne Rechtsform",
  "legal_form": "GmbH / UG / AG / GmbH & Co. KG / etc.",
  "ceo_first_name": "Vorname des Geschäftsführers",
  "ceo_last_name": "Nachname des Geschäftsführers",
  "street": "Straßenname ohne Hausnummer",
  "house_number": "Hausnummer",
  "postal_code": "PLZ",
  "city": "Ort",
  "phone": "Telefonnummer",
  "email": "E-Mail-Adresse",
  "vat_id": "USt-IdNr (z.B. DE123456789)",
  "register_number": "Handelsregisternummer (z.B. HRB 12345)",
  "register_court": "Registergericht (z.B. Amtsgericht Koblenz)",
  "trade": "Branche/Gewerk falls erkennbar"
}}

Felder die nicht gefunden wurden als leeren String "" lassen.
Gib NUR das JSON zurück."""

        response = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1000,
            messages=[{'role': 'user', 'content': prompt}],
        )

        raw = response.content[0].text.strip()

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError('Kein JSON gefunden')

        data = json.loads(match.group())

        cleaned = {k: v for k, v in data.items() if v and v.strip()}

        return {
            'success': True,
            'data': cleaned,
            'impressum_url': website_url,
        }

    except Exception as e:
        logger.error(f'Impressum-Extraktion Fehler: {e}')
        return {
            'success': False,
            'error': f'Extraktion fehlgeschlagen: {str(e)}',
        }
