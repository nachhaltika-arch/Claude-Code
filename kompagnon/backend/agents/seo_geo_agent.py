"""
SEO/GEO Agent: Generate Schema.org structured data and local SEO setup.
Creates JSON-LD, robots.txt, sitemap templates.
"""
import json
import os
from typing import Dict, Optional, List
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class SeoGeoAgent:
    """Generate structured data and local SEO markup."""

    def __init__(self, api_key: Optional[str] = None):
        if not Anthropic:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"

    def generate_seo(self, company_data: Dict) -> Dict:
        """
        Generate complete SEO/GEO setup (Schema.org, robots.txt, sitemap).

        Args:
            company_data: {
                'company_name': str,
                'street': str,
                'postal_code': str,
                'city': str,
                'country': str (default 'DE'),
                'phone': str,
                'email': str,
                'website': str,
                'services': [str],
                'opening_hours': {
                    'monday_friday': 'HH:MM-HH:MM',
                    'saturday': 'HH:MM-HH:MM' or 'closed',
                    'sunday': 'closed' or 'HH:MM-HH:MM',
                },
                'latitude': float,
                'longitude': float,
                'business_type': str (e.g., 'LocalBusiness', 'Plumber'),
            }

        Returns:
            {
                'local_business_schema': Dict (JSON-LD),
                'faq_schema': Dict (JSON-LD for FAQPage),
                'breadcrumb_schema': Dict (JSON-LD),
                'service_schemas': [Dict, ...],
                'robots_txt': str,
                'sitemap_xml_template': str,
                'geo_readiness_score': 0-100,
                'geo_recommendations': [str, ...],
            }
        """
        try:
            system_prompt = """Du bist ein SEO/Geo-Spezialist für KOMPAGNON.
Generiere vollständiges Schema.org-Markup für deutsche Handwerksbetriebe.

WICHTIG:
- Antworte als valides JSON ohne Markdown-Wrapper
- Schema.org muss vollständig, deutschsprachig und korrekt sein
- Alle IDs sind @id URLs in folgendem Format: https://example.com/#[type]
- LocalBusinessSchema: Enthält ALL Kontaktinfos, Öffnungszeiten, Koordinaten
- FaqSchema: JSON-LD für FAQPage mit mainEntity
- Breadcrumb: Home → Services → [Service]
- ServiceSchemas: Eigenes Schema pro Leistung
- geo_readiness_score: Bewertet, wie gut lokal optimiert
- geo_recommendations: Die 5 wichtigsten nächsten Schritte"""

            company_name = company_data.get("company_name", "Betrieb")
            website = company_data.get("website", "https://example.com")

            user_message = f"""
Generiere SEO/GEO-Markup für:

{json.dumps(company_data, indent=2, ensure_ascii=False)}

Liefere das Ergebnis als JSON:
{{
    "local_business_schema": {{ "@context": "https://schema.org", ... }},
    "faq_schema": {{ "@context": "https://schema.org", "@type": "FAQPage", ... }},
    "breadcrumb_schema": {{ "@context": "https://schema.org", ... }},
    "service_schemas": [
        {{ "@context": "https://schema.org", "@type": "Service", ... }},
        ...
    ],
    "robots_txt": "User-agent: *\\nDisallow: /admin\\n...",
    "sitemap_xml_template": "<?xml version=\\"1.0\\"?>\\n<urlset>\\n...",
    "geo_readiness_score": <0-100>,
    "geo_recommendations": [
        "Empfehlung 1",
        "Empfehlung 2",
        ...
    ]
}}"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            response_text = message.content[0].text
            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            return {"error": f"SEO generation failed: {str(e)}"}

    @staticmethod
    def get_mock_seo(company_name: str, city: str) -> Dict:
        """Return mock SEO data for testing."""
        base_url = f"https://example-{city.lower()}.de"

        return {
            "local_business_schema": {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "@id": f"{base_url}/#company",
                "name": company_name,
                "description": f"Professionelle Handwerksleistungen in {city}",
                "url": base_url,
                "telephone": "+49123456789",
                "email": "kontakt@example.de",
                "streetAddress": "Musterstraße 1",
                "addressLocality": city,
                "postalCode": "12345",
                "addressCountry": "DE",
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": 52.5200,
                    "longitude": 13.4050,
                },
                "openingHoursSpecification": [
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                        "opens": "08:00",
                        "closes": "18:00",
                    },
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": "Saturday",
                        "opens": "09:00",
                        "closes": "13:00",
                    },
                ],
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.8",
                    "ratingCount": "127",
                },
            },
            "faq_schema": {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "Wie schnell können Sie kommen?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "In der Regel innerhalb von 2 Stunden.",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Was kostet ein Kostenvoranschlag?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Kostenvoranschläge sind kostenlos. Sie zahlen nur, wenn Sie den Auftrag vergeben.",
                        },
                    },
                ],
            },
            "breadcrumb_schema": {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Startseite",
                        "item": base_url,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Leistungen",
                        "item": f"{base_url}/leistungen",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": "Kontakt",
                        "item": f"{base_url}/kontakt",
                    },
                ],
            },
            "service_schemas": [
                {
                    "@context": "https://schema.org",
                    "@type": "Service",
                    "@id": f"{base_url}/#service-1",
                    "name": "Reparaturservice",
                    "description": "Schnelle Reparaturen 24/7",
                    "provider": {
                        "@type": "LocalBusiness",
                        "name": company_name,
                    },
                    "areaServed": city,
                    "availableChannel": {
                        "@type": "ServiceChannel",
                        "serviceUrl": f"{base_url}/buchung",
                        "servicePhone": "+49123456789",
                    },
                }
            ],
            "robots_txt": """User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /

User-agent: AdsBot-Google
Disallow:

Sitemap: https://example.de/sitemap.xml""",
            "sitemap_xml_template": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:mobile="http://www.google.com/schemas/sitemap-mobile/1.0">
    <url>
        <loc>https://example.de/</loc>
        <lastmod>2025-03-29</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.de/leistungen/</loc>
        <lastmod>2025-03-29</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.de/kontakt/</loc>
        <lastmod>2025-03-29</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>""",
            "geo_readiness_score": 78,
            "geo_recommendations": [
                "Google Business Profile vollständig ausfüllen und verifizieren",
                "Mind. 5 lokale Bewertungen sammeln (Google, ProvenExpert)",
                "Lokale Keywords in Title Tags und Meta Descriptions integrieren",
                "Lokale Backlinks aufbauen (Branchenportale, Kammern)",
                "Regelmäßige Posts und Foto-Updates im Google Business Profil",
            ],
        }
