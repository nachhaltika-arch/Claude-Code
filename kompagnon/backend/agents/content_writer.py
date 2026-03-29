"""
Content Writer Agent: Generate WordPress website copy.
Creates hero, about, services, FAQ, and SEO metadata.
"""
import json
import os
from typing import Dict, Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class ContentWriterAgent:
    """Generate high-converting website copy for handcraft businesses."""

    def __init__(self, api_key: Optional[str] = None):
        if not Anthropic:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"

    def write_content(self, briefing_data: Dict) -> Dict:
        """
        Generate all website copy from briefing data.

        Args:
            briefing_data: {
                'company_name': str,
                'city': str,
                'trade': str,
                'usp': str (unique selling point),
                'services': [str] (list of services),
                'target_audience': str (e.g., "Hausbesitzer in Gröpelingen"),
                'team_size': int,
                'team_info': str (brief team description),
                'years_in_business': int,
                'awards_or_certifications': [str],
            }

        Returns:
            {
                'hero_headline': str (max 8 words),
                'hero_subline': str (1 sentence),
                'about_text': str (150 words),
                'service_texts': {'Service Name': 'Text', ...},
                'faq_items': [{'question': str, 'answer': str}, ...],
                'meta_titles': {'page_name': 'Title Tag', ...},
                'meta_descriptions': {'page_name': 'Description', ...},
                'local_cta': str (regional call-to-action),
            }
        """
        try:
            system_prompt = """Du bist ein Texter für KOMPAGNON, spezialisiert auf deutsche Handwerksbetriebe.
Schreibe konvertierungsstarke, authentische Website-Texte.

WICHTIG:
- Antworte ausschließlich als valides JSON ohne Markdown-Wrapper
- Ton: vertrauenswürdig, bodenständig, kompetent — kein Marketing-Speak
- Integriere den Ortsnamen natürlich in die Texte
- FAQ-Antworten müssen kurz, faktisch und von KI-Suchmaschinen zitierfähig sein
- hero_headline: max. 8 Wörter, Action-focused
- hero_subline: 1 Satz, Nutzen-fokussiert
- about_text: 150 Wörter, Ich-Perspektive ("Wir sind...", "Wir machen...")
- service_texts: Für jede Leistung 80 Wörter, fokussiert auf Vorteile
- faq_items: Mindestens 5, häufige Fragen aus Sicht der Zielgruppe
- meta_titles: max. 60 Zeichen
- meta_descriptions: max. 160 Zeichen
- local_cta: Ein regionaler CTA, der den Ortsnamen enthält"""

            user_message = f"""
Erstelle Website-Texte für diesen Betrieb:

Betrieb: {briefing_data.get('company_name', 'Unbekannt')}
Gewerk: {briefing_data.get('trade', 'Handwerk')}
Stadt: {briefing_data.get('city', 'Lokation')}
USP: {briefing_data.get('usp', 'Keine Angabe')}
Leistungen: {', '.join(briefing_data.get('services', []))}
Zielgruppe: {briefing_data.get('target_audience', 'Lokale Kunden')}
Team: {briefing_data.get('team_info', 'Professionelles Team')}
Betrieb seit: {briefing_data.get('years_in_business', 0)} Jahren
Zertifikate: {', '.join(briefing_data.get('awards_or_certifications', []))}

Liefere das Ergebnis als JSON:
{{
    "hero_headline": "<max. 8 Wörter>",
    "hero_subline": "<1 Satz>",
    "about_text": "<150 Wörter>",
    "service_texts": {{
        "Service 1": "<80 Wörter>",
        "Service 2": "<80 Wörter>"
    }},
    "faq_items": [
        {{"question": "Frage 1?", "answer": "<kurze Antwort>"}},
        {{"question": "Frage 2?", "answer": "<kurze Antwort>"}}
    ],
    "meta_titles": {{
        "homepage": "<max 60 Zeichen>",
        "about": "<max 60 Zeichen>",
        "services": "<max 60 Zeichen>",
        "contact": "<max 60 Zeichen>"
    }},
    "meta_descriptions": {{
        "homepage": "<max 160 Zeichen>",
        "about": "<max 160 Zeichen>",
        "services": "<max 160 Zeichen>",
        "contact": "<max 160 Zeichen>"
    }},
    "local_cta": "<CTA mit Ortsnamen>"
}}"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            response_text = message.content[0].text
            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            return {"error": f"Content generation failed: {str(e)}"}

    @staticmethod
    def get_mock_content(company_name: str, city: str, trade: str) -> Dict:
        """Return mock content for testing (no API call)."""
        return {
            "hero_headline": f"Professionelle {trade}-Arbeiten in {city}",
            "hero_subline": f"Zuverlässige Handwerksleistung mit 15 Jahren Erfahrung — schnell, fair, garantiert.",
            "about_text": f"Wir sind seit 2009 Ihr vertrauenswürdiger Partner für {trade}-Arbeiten in {city} und Umgebung. Unser Team besteht aus lizenzierten Fachleuten, die höchsten Standard setzen. Wir verstehen, dass ein Handwerksbetrieb auf Zuverlässigkeit angewiesen ist. Deshalb arbeiten wir transparent, pünktlich und liefern Qualität, auf die Sie sich verlassen können. Ob Notfall oder Planung — wir sind da. Mit Certified Plus Partnerschaft und Google-Bewertung 4.9★.",
            "service_texts": {
                "Reparaturen": "Schnelle Reparaturen für Notfälle rund um die Uhr. Unser Bereitschaftsteam kommt innerhalb von 2 Stunden. Transparente Kostenvoranschläge vor Beginn der Arbeiten.",
                "Neubau": "Vollständige Installationen für Neubau-Projekte. Wir koordinieren mit Architekt und Bauherr. TÜV-geprüfte Qualität, Herstellergarantien bis zu 5 Jahren.",
                "Wartung": "Jährliche Inspektionen und Wartungsverträge sparen Kosten. Wir dokumentieren alles digital für Sie. Kunden sparen durchschnittlich 30% durch Prävention.",
            },
            "faq_items": [
                {
                    "question": "Wie schnell können Sie bei Notfällen kommen?",
                    "answer": "Unsere Bereitschaft kommt innerhalb von max. 2 Stunden. Anruf genügt, 24/7 verfügbar.",
                },
                {
                    "question": "Was kostet ein Kostenvoranschlag?",
                    "answer": "Kostenvoranschläge sind kostenfrei. Wir machen keine Beratungsgebühren — nur wenn Sie den Auftrag vergeben.",
                },
                {
                    "question": "Haben Sie Garantien?",
                    "answer": "Ja, 2 Jahre auf Arbeit, Herstellergarantien auf Materialien bis zu 5 Jahre.",
                },
                {
                    "question": "Arbeiten Sie auch nachts?",
                    "answer": "Bei Notfällen ja. Nachtzuschlag 25%. Termine nach Absprache.",
                },
                {
                    "question": "Wie bezahle ich?",
                    "answer": "Kasse, Überweisung, EC-Karte. Rechnung nach Fertigstellung.",
                },
            ],
            "meta_titles": {
                "homepage": f"Professionelle {trade} in {city} | Seit 15 Jahren",
                "about": f"Über uns | {company_name} {city}",
                "services": f"Leistungen | {company_name}",
                "contact": f"Kontakt & Terminvergabe | {company_name}",
            },
            "meta_descriptions": {
                "homepage": f"Zuverlässige {trade}-Arbeiten in {city}. Schnell, fair, garantiert. ★ 4.9/5 Google-Bewertung. Kostenvoranschlag online anfordern.",
                "about": f"Lernen Sie das {company_name}-Team kennen. 15 Jahre Erfahrung, TÜV-zertifiziert, über 5000 zufriedene Kunden.",
                "services": f"Reparaturen, Neubau, Wartung — alle {trade}-Leistungen. Jetzt anfragen.",
                "contact": f"Rufen Sie {company_name} an oder buchen Sie einen Termin online. {city} und Umgebung.",
            },
            "local_cta": f"Jetzt kostenlosen Termin in {city} buchen — ein Anruf reicht!",
        }
