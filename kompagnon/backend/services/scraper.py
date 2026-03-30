"""
Website Scraper — Extracts company info from a URL automatically.
Used by the audit endpoint to pre-fill audit data from just a domain.
"""
import re
import httpx
from bs4 import BeautifulSoup


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
            "User-Agent": "Mozilla/5.0 (compatible; KOMPAGNON-Bot/1.0)"
        }

        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True
        ) as client:
            response = await client.get(url, headers=headers)
            html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # 1. Firmenname aus Title oder H1
        title = soup.find("title")
        h1 = soup.find("h1")

        if title:
            company = title.get_text().strip()
            for suffix in [" – ", " | ", " - ", " :: ", " / "]:
                if suffix in company:
                    company = company.split(suffix)[0]
            result["company_name"] = company[:100]

        if h1 and not result["company_name"]:
            result["company_name"] = h1.get_text().strip()[:100]

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
        print(f"Scraping Fehler für {url}: {e}")

    return result
