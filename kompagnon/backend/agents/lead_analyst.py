"""
Lead Analyst Agent: Analyze website and provide sales-ready brief.
Uses Claude API to evaluate digital presence of handcraft businesses.
"""
import json
import os
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
- recommended_approach: Kurzes Pitch-Script (was sagen, worauf hinweisen)"""

            user_message = f"""
Analysiere diese Website:

Unternehmen: {company_name}
Gewerk: {trade}
Stadt: {city}
URL: {website_url}

Website-Daten:
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
        """Fetch basic website info (headers, meta tags, SSL check)."""
        try:
            # Ensure URL has protocol
            if not website_url.startswith(("http://", "https://")):
                website_url = f"https://{website_url}"

            response = requests.get(website_url, timeout=5, allow_redirects=True)

            has_ssl = website_url.startswith("https://")
            has_impressum = "impressum" in response.text.lower()

            return {
                "has_ssl": has_ssl,
                "has_impressum": has_impressum,
                "response_code": response.status_code,
                "content_length": len(response.text),
                "is_mobile_responsive": "viewport" in response.text.lower(),
                "has_images": response.text.count("<img") > 0,
                "has_forms": response.text.count("<form") > 0,
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
