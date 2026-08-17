import asyncio
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

#: Woran ein Impressum zu erkennen ist. Nicht am Wort „Impressum" — das steht
#: in jeder Fusszeile. Sondern an dem, was § 5 DDG verlangt und was sonst
#: nirgends auf einer Handwerkerseite steht.
IMPRESSUM_MERKMALE = (
    'registergericht', 'handelsregister', 'ust-idnr', 'ust.-idnr',
    'umsatzsteuer-identifikationsnummer', 'umsatzsteuer',
    'vertreten durch', 'aufsichtsbehörde', 'aufsichtsbehoerde',
    'kammer', 'berufsbezeichnung', 'inhaltlich verantwortlich',
    'verantwortlich für den inhalt', 'geschäftsführer', 'geschaeftsfuehrer',
)

#: Kürzer als das ist keine Pflichtangabe, sondern ein Menüpunkt. Die Schwelle
#: trennt nicht Hülle von Impressum — das tun die Merkmale. Sie hält nur
#: Schnipsel raus.
IMPRESSUM_MINDESTLAENGE = 120

#: Jeder Kandidat kostet einen Abruf. Mehr als das dauert länger, als
#: irgendjemand auf eine Antwort wartet.
MAX_KANDIDATEN = 12


def wirkt_wie_impressum(text) -> bool:
    """Ist das ein Impressum — oder nur eine Seite, auf der das Wort steht?

    Bis zum 17.08.2026 fragte der Sucher nur „mehr als 100 Zeichen?". Bei
    `alkozei.de` lieferte `/impressum` die Hülle der Anwendung: 2597 Zeichen
    Navigation, kein einziger Pflichthinweis. Sie bestand die Prüfung, und die
    richtige Seite wurde nie geholt.

    Eine Längenschwelle beantwortet „ist da Text?". Gefragt war „ist das das
    Richtige?".
    """
    if not text or len(text) < IMPRESSUM_MINDESTLAENGE:
        return False
    klein = text.lower()
    return any(merkmal in klein for merkmal in IMPRESSUM_MERKMALE)


def impressum_kandidaten(website_url: str, html: str) -> list:
    """Mögliche Adressen des Impressums, in der Reihenfolge des Zutrauens.

    **Warum das mehr ist als „dem Link folgen".** Auf `alkozei.de` steht in
    der Startseite:

        <a href="impressum" onclick="return false;" data-nbito-call-page="3">

    Der Verweis ist absichtlich tot — die Navigation macht JavaScript. Wer ihm
    folgt, landet auf `/impressum` und bekommt die Hülle. Das Impressum liegt
    unter `/now.using/nBito/impressum`, und dieser Anwendungspfad **steht im
    Quelltext**, nur eben nicht im `href`.

    Deshalb drei Quellen: die Verweise selbst, dieselben Verweise unter jedem
    im Quelltext gefundenen Anwendungspfad, und zuletzt die bekannten festen
    Pfade.
    """
    from urllib.parse import urljoin, urlparse

    basis = website_url.rstrip('/')
    if not basis.startswith('http'):
        basis = 'https://' + basis
    eigene_domain = urlparse(basis).netloc.split(':')[0].replace('www.', '')

    kandidaten = []

    def merken(url: str) -> None:
        if not url or len(kandidaten) >= MAX_KANDIDATEN:
            return
        # Fremde Domains gehören einem anderen — der Impressum-Link einer
        # Agentur führt auf deren Impressum, nicht auf das des Betriebs.
        domain = urlparse(url).netloc.split(':')[0].replace('www.', '')
        if domain and domain != eigene_domain:
            return
        if url not in kandidaten:
            kandidaten.append(url)

    verweise = [
        v for v in re.findall(r'href=["\']([^"\']*?)["\']', html or '', re.IGNORECASE)
        if any(wort in v.lower() for wort in ('impressum', 'imprint', 'legal', 'rechtlich'))
    ]

    for verweis in verweise:
        merken(urljoin(basis + '/', verweis))

    # Anwendungspfade aus dem Quelltext — dort, wo der tote Verweis hinführen
    # würde, wenn JavaScript liefe.
    anwendungspfade = set()
    for treffer in re.findall(r'["\']([a-zA-Z0-9_.\-]+/[a-zA-Z0-9_.\-]+)/[a-zA-Z0-9_.\-]+["\']', html or ''):
        if treffer.count('/') == 1 and not treffer.startswith('http'):
            anwendungspfade.add(treffer)

    for pfad in sorted(anwendungspfade):
        for verweis in verweise:
            if not verweis.startswith('http') and '/' not in verweis:
                merken(f"{basis}/{pfad}/{verweis}")

    for pfad in IMPRESSUM_PATHS:
        merken(basis + pfad)

    return kandidaten


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

    bester_rueckfall = ''

    async with httpx.AsyncClient(timeout=10, follow_redirects=True, verify=False) as client:
        # Die Startseite liefert die Verweise und die Anwendungspfade.
        startseite = ''
        try:
            res = await client.get(base, headers=headers)
            startseite = res.text
            bester_rueckfall = clean_html(startseite)
        except Exception as fehler:  # noqa: BLE001 — ohne Startseite bleiben die festen Pfade
            logger.debug(f"Startseite {base} nicht erreichbar: {fehler}")

        for kandidat in impressum_kandidaten(base, startseite):
            try:
                antwort = await client.get(kandidat, headers=headers)
            except Exception:  # noqa: BLE001 — der nächste Kandidat ist einen Versuch wert
                continue
            if antwort.status_code != 200:
                continue

            text = clean_html(antwort.text)

            # Hier wurde bis zum 17.08.2026 die erste Seite über 100 Zeichen
            # genommen. Jetzt entscheidet, ob es *aussieht* wie ein Impressum.
            if wirkt_wie_impressum(text):
                logger.info(f"Impressum gefunden: {kandidat} ({len(text)} Zeichen)")
                return text[:8000]

            if len(text) > len(bester_rueckfall):
                bester_rueckfall = text

    # Nichts hat die Prüfung bestanden. Der längste gefundene Text ist besser
    # als nichts: Bei `alkozei.de` stehen Firmenname, Anschrift und Telefon
    # auch auf der Startseite. Der Aufrufer bekommt also Daten, nur eben ohne
    # die Pflichtangaben.
    if bester_rueckfall:
        logger.info(f"Kein Impressum erkannt für {base} — Rückfall auf {len(bester_rueckfall)} Zeichen")
    return bester_rueckfall[:8000] if bester_rueckfall else ''


def extract_favicon_from_html(html: str, base_url: str) -> str:
    """Extract favicon URL from HTML <head> link tags. Returns absolute URL or ''."""
    base = base_url.rstrip('/')
    # Look for <link rel="icon"> or <link rel="shortcut icon">
    pattern = re.compile(
        r'<link[^>]+rel=["\'](?:shortcut icon|icon)["\'][^>]*href=["\']([^"\']+)["\']'
        r'|<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\'](?:shortcut icon|icon)["\']',
        re.IGNORECASE,
    )
    for m in pattern.finditer(html):
        href = m.group(1) or m.group(2)
        if not href:
            continue
        if href.startswith('http'):
            return href
        if href.startswith('//'):
            return 'https:' + href
        if href.startswith('/'):
            return base + href
        return base + '/' + href
    return ''


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
        import anthropic
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), max_retries=0)

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

        try:
            # `Anthropic` ist der SYNCHRONE Client. Direkt in einer `async def`
            # aufgerufen hält er die Ereignisschleife an — bis zu zwanzig
            # Sekunden, in denen der Server auf nichts mehr antwortet, auch
            # nicht auf die Gesundheitsprüfung von Render. Deren Proxy kappte
            # daraufhin die laufende Anfrage: 503, im Browser „Failed to
            # fetch", in der Oberfläche „Verbindungsfehler". Der Fehler sah aus
            # wie ein Netzproblem und war ein Nebenläufigkeitsproblem
            # (17.08.2026, mit David am Bildschirm gefunden).
            response = await asyncio.to_thread(
                lambda: client.messages.create(
                    model='claude-sonnet-4-6',
                    max_tokens=1000,
                    messages=[{'role': 'user', 'content': prompt}],
                    timeout=20.0,
                )
            )
        except anthropic.APIStatusError as api_err:
            if api_err.status_code == 529:
                logger.warning('Anthropic überlastet — Impressum-Extraktion übersprungen')
                return {'success': False, 'error': 'API überlastet'}
            raise
        except anthropic.APITimeoutError:
            logger.warning('Anthropic Timeout — übersprungen')
            return {'success': False, 'error': 'Timeout'}

        raw = response.content[0].text.strip()

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError('Kein JSON gefunden')

        data = json.loads(match.group())

        # `v.strip()` auf einer Zahl wäre ein AttributeError — und der landete
        # im äußeren `except`, das jeden Fehler zu „Extraktion fehlgeschlagen"
        # macht. Eine Postleitzahl als Zahl darf die Auswertung nicht kippen.
        cleaned = {}
        for schluessel, wert in data.items():
            text = str(wert).strip() if wert is not None else ''
            if text:
                cleaned[schluessel] = text

        antwort = {
            'success': True,
            'data': cleaned,
            'impressum_url': website_url,
        }

        # Nichts gefunden, obwohl Text da war — dann muss die Antwort sagen,
        # woran es lag. Bei `gleichstrom.de` stand am 17.08.2026 alles im
        # Impressum und die Auswertung gab trotzdem nichts zurück; ohne diese
        # Angaben war nicht feststellbar, ob das Modell, der Text oder das
        # Auslesen schuld war (kein lokaler Schlüssel, keine Logs von hier).
        if not cleaned:
            logger.warning(
                f"Impressum ausgelesen, aber nichts extrahiert für {website_url} "
                f"({len(impressum_text)} Zeichen Text) — Modellantwort: {raw[:200]}"
            )
            antwort['roh_antwort'] = raw[:300]
            antwort['text_laenge'] = len(impressum_text)

        return antwort

    except Exception as e:
        logger.error(f'Impressum-Extraktion Fehler: {e}')
        return {
            'success': False,
            'error': f'Extraktion fehlgeschlagen: {str(e)}',
        }
