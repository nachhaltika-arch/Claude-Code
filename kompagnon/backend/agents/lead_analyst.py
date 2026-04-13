"""
Lead Analyst Agent: Analyze website and provide sales-ready brief.
Uses Claude API to evaluate digital presence of handcraft businesses.
"""
import json
import os
import re
import time
from typing import Dict, Optional
import requests

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class LeadAnalystAgent:
    """Analyze lead's website and provide scoring + sales brief."""

    def __init__(self, api_key: Optional[str] = None):
        if not Anthropic:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"

    def analyze_lead(
        self,
        website_url: str,
        company_name: str,
        city: str,
        trade: str,
    ) -> Dict:
        """
        Analyze lead's website and return structured scoring.

        Args:
            website_url: URL to analyze
            company_name: Company name
            city: City/location
            trade: Trade/industry (e.g., "Klempner", "Elektrik")

        Returns:
            {
                'overall_score': 0-100,
                'website_age_estimate': 'months' str,
                'mobile_score': 0-100,
                'performance_score': 0-100,
                'has_ssl': bool,
                'has_impressum': bool,
                'geo_visibility_score': 0-10,
                'top_3_issues': [str, str, str],
                'opportunity_summary': str (2-3 sentences),
                'recommended_approach': str (brief pitch script),
                'analysis_timestamp': ISO timestamp
            }
        """
        try:
            # Prepare context
            website_info = self._fetch_website_info(website_url)

            system_prompt = """Du bist ein Website-Analyst für KOMPAGNON, ein Webdesign-Service für deutsche Handwerksbetriebe.
Analysiere die gegebenen Website-Daten und erstelle eine prägnante Bewertung der digitalen Präsenz.

WICHTIG:
- Antworte ausschließlich als valides JSON ohne Markdown-Wrapper
- Antworte auf Deutsch
- Sei konkret, faktenbasiert und praxisorientiert
- Fokus: Was fehlt, was kostet den Betrieb Kunden, wo liegt die größte Chance?
- overall_score: 0-100, basierend auf mobile_score, performance_score, SSL, Impressum
- geo_visibility_score: 0-10 (simuliert, basierend auf Adresse-Nennung, Local SEO Signale)
- top_3_issues: Die 3 größten Probleme (fehlende Features, Performance, Mobile, SEO)
- opportunity_summary: 2-3 Sätze für den Vertriebler
- recommended_approach: Kurzes Pitch-Script (was sagen, worauf hinweisen)

SCHATZ-HINWEIS fuer mobile_score und performance_score:
Die uebergebenen Website-Daten enthalten keine echten PageSpeed-Messwerte —
echte Lighthouse-Zahlen kommen spaeter aus der Analyse-Zentrale.
Schaetze diese beiden Scores auf Basis der load_time_ms (je niedriger desto
besser) und der technischen Signale (viewport-Meta, Bildzahl, Analytics,
strukturierte Daten, interne Verlinkung). Nenne die Schaetzung intuitiv
plausibel, nicht aggressive Werte. Hinweis: load_time_ms < 1000 = sehr gut,
1000-3000 = akzeptabel, > 3000 = traege."""

            user_message = f"""
Analysiere diese Website:

Unternehmen: {company_name}
Gewerk: {trade}
Stadt: {city}
URL: {website_url}

Wichtige Signale:
  Seiten-Titel: {website_info.get('page_title', '–') or '–'}
  Meta-Beschreibung: {website_info.get('meta_description', '–') or '–'}
  H1: {website_info.get('h1_text', '–') or '–'} ({website_info.get('h1_count', 0)}x)
  Ladezeit: {website_info.get('load_time_ms', '–')} ms
  Google Analytics: {'vorhanden' if website_info.get('has_google_analytics') else 'nicht vorhanden'}
  Telefonnummer sichtbar: {'ja' if website_info.get('has_phone_number') else 'nein'}
  Strukturierte Daten (Schema.org): {'vorhanden' if website_info.get('has_structured_data') else 'fehlt'}
  Interne Links: {website_info.get('internal_links_count', 0)}
  Bilder: {website_info.get('image_count', 0)}

Rohdaten:
{json.dumps(website_info, indent=2, ensure_ascii=False)}

Liefere das Analyse-Ergebnis als JSON mit folgender Struktur:
{{
    "overall_score": <0-100>,
    "website_age_estimate": "<Schätzung z.B. '6 Monate'>",
    "mobile_score": <0-100>,
    "performance_score": <0-100>,
    "has_ssl": <true/false>,
    "has_impressum": <true/false>,
    "geo_visibility_score": <0-10>,
    "top_3_issues": ["Issue 1", "Issue 2", "Issue 3"],
    "opportunity_summary": "<2-3 Sätze>",
    "recommended_approach": "<Pitch-Script>"
}}"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract and parse JSON
            response_text = message.content[0].text
            result = json.loads(response_text)

            # Ensure required fields
            result.setdefault("analysis_timestamp", self._get_timestamp())
            return result

        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parse error: {str(e)}",
                "overall_score": 0,
                "mobile_score": 0,
                "performance_score": 0,
            }
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "overall_score": 0,
                "mobile_score": 0,
                "performance_score": 0,
            }

    def _fetch_website_info(self, website_url: str) -> Dict:
        """Fetch website info: headers, meta tags, SEO signals, load time.

        Parst alles lokal aus dem HTML ohne externe API. Jeder Parse-Schritt
        ist in sein eigenes try/except gekapselt, damit ein einzelner Fehler
        (z.B. kaputter <title>-Tag) nicht die gesamte Analyse crashen laesst
        — stattdessen bekommt das einzelne Feld seinen Default-Wert.
        """
        try:
            # Ensure URL has protocol
            if not website_url.startswith(("http://", "https://")):
                website_url = f"https://{website_url}"

            start = time.time()
            response = requests.get(website_url, timeout=8, allow_redirects=True)
            load_time_ms = round((time.time() - start) * 1000)

            html = response.text
            html_lower = html.lower()

            def _strip_tags(s: str) -> str:
                return re.sub(r'<[^>]+>', '', s).strip()

            # Basis-Signale
            has_ssl = website_url.startswith("https://")
            has_impressum = "impressum" in html_lower
            is_mobile_responsive = "viewport" in html_lower

            # Page-Title
            page_title = ""
            try:
                m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                if m:
                    page_title = _strip_tags(m.group(1))[:100]
            except Exception:
                page_title = ""

            # Meta-Description (sowohl name= als auch property=og:description-Fallback)
            meta_description = ""
            try:
                m = re.search(
                    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
                    html, re.IGNORECASE,
                )
                if not m:
                    m = re.search(
                        r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
                        html, re.IGNORECASE,
                    )
                if m:
                    meta_description = m.group(1).strip()[:200]
            except Exception:
                meta_description = ""

            # H1
            h1_text = ""
            h1_count = 0
            try:
                h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
                h1_count = len(h1_matches)
                if h1_matches:
                    h1_text = _strip_tags(h1_matches[0])[:100]
            except Exception:
                h1_text = ""
                h1_count = 0

            # Bild-Count
            try:
                image_count = len(re.findall(r'<img\b', html, re.IGNORECASE))
            except Exception:
                image_count = 0
            has_images = image_count > 0

            # Form-Count
            try:
                has_forms = bool(re.search(r'<form\b', html, re.IGNORECASE))
            except Exception:
                has_forms = False

            # Google Analytics / GA4 / UA / Tag Manager
            try:
                has_google_analytics = bool(
                    re.search(r'gtag\s*\(|ga\s*\(|UA-\d+|G-[A-Z0-9]+|googletagmanager', html)
                )
            except Exception:
                has_google_analytics = False

            # Telefon (deutsches Format, sowohl +49 als auch 0xxx)
            try:
                has_phone_number = bool(
                    re.search(r'(\+49|0\d{2,4})[\s\-/]?\d{3,}', html)
                )
            except Exception:
                has_phone_number = False

            # Interne Links (relative hrefs) — begrenzt robust: href="/..." oder href="xyz"
            # (ohne Protokoll). Externe: href="http..." werden ausgelassen.
            try:
                internal_links_count = len(
                    re.findall(r'<a\b[^>]+href=["\'](?!https?://|mailto:|tel:|#)[^"\']+["\']',
                               html, re.IGNORECASE)
                )
            except Exception:
                internal_links_count = 0

            # Schema.org / JSON-LD
            has_structured_data = "application/ld+json" in html_lower

            return {
                "has_ssl": has_ssl,
                "has_impressum": has_impressum,
                "response_code": response.status_code,
                "content_length": len(html),
                "is_mobile_responsive": is_mobile_responsive,
                "has_images": has_images,
                "has_forms": has_forms,
                # Neu:
                "page_title": page_title,
                "meta_description": meta_description,
                "h1_text": h1_text,
                "h1_count": h1_count,
                "image_count": image_count,
                "has_google_analytics": has_google_analytics,
                "has_phone_number": has_phone_number,
                "internal_links_count": internal_links_count,
                "has_structured_data": has_structured_data,
                "load_time_ms": load_time_ms,
            }
        except Exception as e:
            return {
                "error": f"Could not fetch: {str(e)}",
                "has_ssl": False,
                "has_impressum": False,
            }

    @staticmethod
    def _get_timestamp() -> str:
        """Get ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def get_mock_analysis(company_name: str, trade: str) -> Dict:
        """Return mock analysis for testing (no API call)."""
        return {
            "overall_score": 52,
            "website_age_estimate": "8 Monate",
            "mobile_score": 48,
            "performance_score": 56,
            "has_ssl": True,
            "has_impressum": True,
            "geo_visibility_score": 4,
            "top_3_issues": [
                "Mobile Performance unzureichend (<50 PageSpeed)",
                "Keine FAQ oder lokale Service-Beschreibungen",
                "Keine vertrauensaufbauenden Elemente (Bewertungen, Zertifikate)",
            ],
            "opportunity_summary": f"{company_name} hat eine solide Basis, aber Optimierungspotential bei Mobile-Performance und lokaler SEO. Mit KOMPAGNON könnten 25-40% mehr Anfragen generiert werden.",
            "recommended_approach": "Hallo [Name], ich bin von KOMPAGNON, wir spezialisieren uns auf WordPress-Websites für {trade}-Betriebe. Ich habe [Company] analysiert — großartig, dass Sie online sind! Kleine Idee: Ihre Website könnte auf Mobilgeräten noch flüssiger laufen, das kostet Sie wahrscheinlich Kunden. Wir könnten das in 2 Wochen für 2.000€ fixed price beheben.",
            "analysis_timestamp": LeadAnalystAgent._get_timestamp(),
        }
