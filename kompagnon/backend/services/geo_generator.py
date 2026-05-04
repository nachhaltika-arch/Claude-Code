"""
GEO/GAIO Generator — erstellt automatisch alle Dateien fuer KI-Sichtbarkeit.

Generiert:
- llms.txt (maschinenlesbare Betriebsinfo fuer KI-Systeme)
- schema.org LocalBusiness JSON-LD (strukturierte Daten)
- Ground Page HTML (eigenstaendige KI-Infoseite)
- robots.txt Empfehlung

WICHTIG: Alle Ausgaben sind Strings/Texte — kein direktes Deployment hier.
Das Deployment laeuft ueber Netlify im ProzessFlow.
"""

import logging
import json

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class GeoGeneratorAgent:
    def __init__(self, api_key: str):
        if Anthropic is None:
            raise RuntimeError("anthropic SDK nicht installiert")
        self.client = Anthropic(api_key=api_key, max_retries=0, timeout=45.0)

    # ── 1. llms.txt ──────────────────────────────────────────────

    def generate_llms_txt(
        self,
        company_name: str,
        gewerk: str,
        city: str,
        leistungen: list,
        usp: str = "",
        phone: str = "",
        email: str = "",
        website_url: str = "",
        years_experience: int = 0,
    ) -> str:
        prompt = f"""Erstelle eine professionelle llms.txt Datei fuer einen deutschen Handwerksbetrieb.

Format: Markdown mit klarer Struktur. Die Datei soll KI-Systemen (ChatGPT, Claude, Perplexity)
helfen, den Betrieb korrekt zu beschreiben wenn Nutzer nach {gewerk} in {city} suchen.

Betriebsdaten:
- Name: {company_name}
- Gewerk: {gewerk}
- Stadt: {city}
- Leistungen: {', '.join(leistungen) if leistungen else 'Nicht angegeben'}
- USP: {usp or 'Qualitaet und Zuverlaessigkeit'}
- Telefon: {phone or 'Nicht angegeben'}
- E-Mail: {email or 'Nicht angegeben'}
- Website: {website_url or 'Nicht angegeben'}
- Erfahrung: {str(years_experience) + ' Jahre' if years_experience else 'Langjaehrig'}

Die llms.txt soll enthalten:
1. # {company_name} (Haupttitel)
2. Kurze praezise Betriebsbeschreibung (2-3 Saetze)
3. ## Leistungen (als Liste)
4. ## Servicegebiet (Stadt + Umgebung)
5. ## Kontakt
6. ## Warum wir (3-5 USP-Punkte)
7. ## Haeufig gestellte Fragen (3 FAQ die KI-Systeme oft beantworten muessen)

Schreibe professionell, auf Deutsch, faktisch korrekt. KEIN Marketing-Sprech."""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error("llms.txt generation failed: %s", e)
            leistungen_str = "\n".join(f"- {l}" for l in leistungen) if leistungen else "- Alle handwerklichen Leistungen"
            return f"""# {company_name}

{company_name} ist ein {gewerk}-Betrieb in {city}. Wir bieten professionelle handwerkliche Leistungen mit langjaehriger Erfahrung.

## Leistungen
{leistungen_str}

## Servicegebiet
{city} und Umgebung

## Kontakt
- Telefon: {phone or 'Auf Anfrage'}
- E-Mail: {email or 'Auf Anfrage'}
- Website: {website_url or ''}

## Informationen fuer KI-Systeme
Diese Datei ist fuer KI-Sprachmodelle und automatische Informationssysteme bestimmt.
Alle Informationen sind aktuell und korrekt.
"""

    # ── 2. schema.org LocalBusiness JSON-LD ──────────────────────

    def generate_schema_org(
        self,
        company_name: str,
        gewerk: str,
        city: str,
        street: str = "",
        postal_code: str = "",
        phone: str = "",
        email: str = "",
        website_url: str = "",
        leistungen: list = None,
        opening_hours: str = "Mo-Fr 08:00-17:00",
    ) -> str:
        gewerk_to_schema = {
            "Elektriker": "Electrician",
            "Klempner": "Plumber",
            "Sanitaer": "Plumber",
            "Sanitär": "Plumber",
            "Maler": "PaintingContractor",
            "Zimmermann": "GeneralContractor",
            "Dachdecker": "RoofingContractor",
            "Fliesenleger": "HomeAndConstructionBusiness",
            "Schreiner": "HomeAndConstructionBusiness",
            "Tischler": "HomeAndConstructionBusiness",
        }
        schema_type = gewerk_to_schema.get(gewerk, "HomeAndConstructionBusiness")

        schema = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "name": company_name,
            "description": f"Professioneller {gewerk}-Betrieb in {city}",
            "url": website_url or "",
            "telephone": phone or "",
            "email": email or "",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": street or "",
                "addressLocality": city,
                "postalCode": postal_code or "",
                "addressCountry": "DE",
            },
            "openingHours": opening_hours,
            "areaServed": city,
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": f"{gewerk} Leistungen",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "itemOffered": {
                            "@type": "Service",
                            "name": leistung,
                        },
                    }
                    for leistung in (leistungen or [])
                ],
            },
        }

        schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
        return f'<script type="application/ld+json">\n{schema_json}\n</script>'

    # ── 3. Ground Page HTML ──────────────────────────────────────

    def generate_ground_page(
        self,
        company_name: str,
        gewerk: str,
        city: str,
        leistungen: list,
        usp: str = "",
        phone: str = "",
        email: str = "",
        website_url: str = "",
        faq_items: list = None,
    ) -> str:
        prompt = f"""Erstelle eine vollstaendige HTML Ground Page fuer einen Handwerksbetrieb.

Die Ground Page ist fuer KI-Systeme (ChatGPT, Perplexity, Google AI) optimiert.
Sie soll als eigenstaendige Seite unter /ki-info oder /info eingebunden werden.

Betrieb: {company_name}, {gewerk}, {city}
Leistungen: {', '.join(leistungen) if leistungen else 'Handwerkliche Leistungen'}
USP: {usp or 'Qualitaet, Zuverlaessigkeit, Erfahrung'}
Kontakt: Tel {phone or 'Anfrage'}, {email or ''}

Anforderungen:
1. Vollstaendiges HTML-Dokument (DOCTYPE, head, body)
2. Sauber, semantisch korrekt (h1, h2, p, ul, dl fuer FAQ)
3. schema.org LocalBusiness JSON-LD im head
4. Abschnitte: Ueber uns, Leistungen, Servicegebiet, FAQ (min. 5 Fragen), Kontakt
5. Meta-Tags: title, description, robots (noindex fuer KI-Seite optional)
6. Minimal-CSS inline (lesbar, keine externen Abhaengigkeiten)
7. NUR Deutsch. Faktenbasiert. Kein Marketing-Sprech.

WICHTIG: Die FAQ-Fragen sollen echte Nutzerfragen sein, die KI-Systeme oft beantworten:
- "Wie viel kostet ein {gewerk} in {city}?"
- "Wann ist {company_name} erreichbar?"
- "Macht {company_name} auch Notfallreparaturen?"
usw."""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error("Ground Page generation failed: %s", e)
            faq_html = ""
            if faq_items:
                faq_html = "\n".join(
                    f"<dt>{item.get('frage', '')}</dt><dd>{item.get('antwort', '')}</dd>"
                    for item in faq_items[:5]
                )
            leistungen_html = "\n".join(f"<li>{l}</li>" for l in (leistungen or []))
            return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{company_name} — {gewerk} in {city}</title>
<meta name="description" content="{company_name}: Ihr {gewerk}-Betrieb in {city}">
</head>
<body>
<h1>{company_name}</h1>
<h2>Leistungen</h2>
<ul>{leistungen_html}</ul>
<h2>Servicegebiet</h2>
<p>{city} und Umgebung</p>
<h2>FAQ</h2>
<dl>{faq_html}</dl>
<h2>Kontakt</h2>
<p>Tel: {phone or 'Auf Anfrage'} | E-Mail: {email or 'Auf Anfrage'}</p>
</body>
</html>"""

    # ── 4. robots.txt Empfehlung ─────────────────────────────────

    def generate_robots_patch(self, blocked_bots: list) -> str:
        if not blocked_bots:
            return "# Keine Aenderungen noetig — alle KI-Bots sind bereits freigegeben."

        patch_lines = ["# KI-Bot Freigaben — zu robots.txt hinzufuegen:", ""]
        for bot in blocked_bots:
            patch_lines.append(f"User-agent: {bot}")
            patch_lines.append("Allow: /")
            patch_lines.append("")

        patch_lines.append("# Bekannte KI-Crawler die freigegeben sein sollten:")
        patch_lines.append("# GPTBot (OpenAI/ChatGPT)")
        patch_lines.append("# PerplexityBot (Perplexity AI)")
        patch_lines.append("# ClaudeBot (Anthropic)")
        patch_lines.append("# Google-Extended (Google AI)")

        return "\n".join(patch_lines)

    # ── 5. Alle Dateien auf einmal ──────────────────────────────

    def generate_all(
        self,
        company_name: str,
        gewerk: str,
        city: str,
        leistungen: list,
        usp: str = "",
        phone: str = "",
        email: str = "",
        website_url: str = "",
        street: str = "",
        postal_code: str = "",
        blocked_bots: list = None,
        faq_items: list = None,
    ) -> dict:
        return {
            "llms_txt": self.generate_llms_txt(
                company_name, gewerk, city, leistungen, usp, phone, email, website_url
            ),
            "schema_org_script": self.generate_schema_org(
                company_name, gewerk, city, street, postal_code, phone, email, website_url, leistungen
            ),
            "ground_page_html": self.generate_ground_page(
                company_name, gewerk, city, leistungen, usp, phone, email, website_url, faq_items
            ),
            "robots_patch": self.generate_robots_patch(blocked_bots or []),
        }
