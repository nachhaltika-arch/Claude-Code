"""
Website Scraper — Extracts company info from a URL automatically.
Used by the audit endpoint to pre-fill audit data from just a domain.
"""
import logging
import re
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Seitentitel, die keinen Betrieb benennen. Ohne diese Prüfung wurde der Titel
# blind übernommen — und der Bericht aus dem Widget sprach den Empfänger dann
# mit „Analyse für Startseite" an. Lieber gar kein Name als ein falscher: der
# Aufrufer fällt dann auf die Domain zurück.
PLATZHALTER_TITEL = frozenset({
    "startseite", "start", "home", "homepage", "willkommen",
    "herzlich willkommen", "index", "unbenanntes dokument", "unbenannt",
    "neue seite", "website", "webseite", "hauptseite", "menü", "menu",
})

# Reihenfolge zählt: der lange Gedankenstrich vor dem kurzen Bindestrich,
# sonst zerschneidet „Müller-Bau - Startseite" den Firmennamen selbst.
TITEL_TRENNER = (" – ", " — ", " | ", " · ", " :: ", " / ", " - ")

MIN_NAMENSLAENGE = 2
MAX_NAMENSLAENGE = 100


def firmenname_aus_titel(titel: str) -> str:
    """Der Firmenname aus einem Seitentitel — oder leer, wenn keiner drinsteht.

    Der Titel wird am ersten Trenner abgeschnitten, weil dahinter fast immer
    ein Werbesatz steht. Bleibt danach ein Platzhalter übrig, gilt das als
    „nicht gefunden" — ein falscher Name ist in der Anrede schlimmer als keiner.
    """
    name = (titel or "").strip()
    for trenner in TITEL_TRENNER:
        if trenner in name:
            name = name.split(trenner)[0].strip()
            break

    if len(name) < MIN_NAMENSLAENGE or name.lower() in PLATZHALTER_TITEL:
        return ""
    return name[:MAX_NAMENSLAENGE]


def firmenname_fuer_audit(angegeben: str, gescrapt: str, url: str) -> str:
    """Mit diesem Namen wird der Empfänger im Bericht und in der Mail angesprochen.

    Reihenfolge: was der Aufrufer weiß, dann was auf der Seite steht, zuletzt
    die blanke Domain. Die volle Adresse war hier früher der letzte Rückfall —
    „Ihre Website-Analyse für https://example.de/" liest sich wie ein Fehler.
    """
    name = (angegeben or "").strip() or (gescrapt or "").strip()
    if name:
        return name[:MAX_NAMENSLAENGE]

    ohne_schema = (url or "").split("//", 1)[-1]
    return ohne_schema.split("/")[0].removeprefix("www.")


async def scrape_website(url: str) -> dict:
    """
    Scrapt eine Website und extrahiert automatisch:
    - Firmenname
    - Telefonnummer
    - E-Mail
    - Adresse / Stadt
    - Branche / Gewerk
    - Beschreibung
    """
    if not url.startswith("http"):
        url = "https://" + url

    result = {
        "website_url": url,
        "company_name": "",
        "phone": "",
        "email": "",
        "city": "",
        "trade": "Sonstiges",
        "description": "",
        "has_impressum": False,
        "has_datenschutz": False,
        "meta_description": "",
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        async with httpx.AsyncClient(
            timeout=8.0, follow_redirects=True, verify=False
        ) as client:
            response = await client.get(url, headers=headers)

        if response.status_code in (403, 429):
            # Website blockiert automatisches Scraping — Fallback-Daten verwenden
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lstrip("www.")
            result["company_name"] = domain
            result["has_ssl"] = url.startswith("https://")
            result["_scraping_blocked"] = True
            return result

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Firmenname aus Title oder H1
        title = soup.find("title")
        h1 = soup.find("h1")

        if title:
            result["company_name"] = firmenname_aus_titel(title.get_text())

        if h1 and not result["company_name"]:
            result["company_name"] = firmenname_aus_titel(h1.get_text())

        # 2. Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            result["meta_description"] = meta_desc.get("content", "")[:300]

        # 3. Telefonnummer
        text = soup.get_text()
        phone_patterns = [
            r'(?:Tel|Telefon|Phone|Fon|Ruf)[\s.:]*(\+?[\d\s\-\/\(\)]{8,20})',
            r'(\+49[\s\-\d]{8,20})',
            r'(0[\d]{2,5}[\s\-\/][\d\s\-]{4,15})',
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phone = re.sub(r'\s+', ' ', match.group(1).strip())
                result["phone"] = phone[:30]
                break

        # 4. E-Mail
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        if emails:
            preferred = [
                e for e in emails
                if any(p in e.lower() for p in [
                    "info", "kontakt", "contact", "mail", "office", "hallo"
                ])
            ]
            result["email"] = preferred[0] if preferred else emails[0]

        # 5. Stadt aus Adresse (PLZ + Ortsname)
        city_patterns = [
            r'\b(\d{5})\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s[A-ZÄÖÜ][a-zäöüß]+)?)',
        ]
        for pattern in city_patterns:
            match = re.search(pattern, text)
            if match:
                result["city"] = match.group(2).strip()
                break

        # 6. Gewerk / Branche erkennen
        trade_keywords = {
            "Elektriker": [
                "elektro", "elektriker", "elektrotechnik", "strom", "installation"
            ],
            "Klempner": [
                "klempner", "sanitär", "heizung", "rohr", "wasser"
            ],
            "Maler": [
                "maler", "lackierer", "anstreicher", "farbe", "tapete"
            ],
            "Schreiner": [
                "schreiner", "tischler", "holz", "möbel", "zimmerei"
            ],
            "Dachdecker": [
                "dachdecker", "dach", "bedachung", "ziegel", "dacharbeiten"
            ],
            "Fliesenleger": [
                "fliesen", "fliesenleger", "kacheln"
            ],
            "Maurer": [
                "maurer", "bau", "bauunternehmen", "hochbau", "tiefbau"
            ],
            "Garten": [
                "garten", "landschaft", "grünanlage", "rasenpflege"
            ],
            "Reinigung": [
                "reinigung", "gebäudereinigung", "hausmeister"
            ],
        }

        text_lower = text.lower()
        for trade, keywords in trade_keywords.items():
            if any(kw in text_lower for kw in keywords):
                result["trade"] = trade
                break

        # 7. Impressum & Datenschutz prüfen
        links = [a.get("href", "").lower() for a in soup.find_all("a", href=True)]
        result["has_impressum"] = any("impressum" in l for l in links)
        result["has_datenschutz"] = any(
            "datenschutz" in l or "privacy" in l for l in links
        )

    except Exception as e:
        logger.error(f"Scraping Fehler für {url}: {e}")

    return result
