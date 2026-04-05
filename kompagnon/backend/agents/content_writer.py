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
                'usp': str,
                'services': [str],
                'target_audience': str,
                'page_name': str  (optional, e.g. "Startseite"),
                'zweck': str      (optional, page purpose),
                'ziel_keyword': str (optional, SEO keyword),
                'cta_text': str   (optional, CTA text),
                'content_*': str  (optional, pre-written slot texts),
                'team_size': int,
                'team_info': str,
                'years_in_business': int,
                'awards_or_certifications': [str],
            }
        """
        try:
            # Collect pre-written content slots (keys starting with "content_")
            content_slots = {
                k: v for k, v in briefing_data.items()
                if k.startswith('content_') and v
            }
            content_slots_text = ''
            if content_slots:
                lines = [f'  {k.replace("content_", "")}: {v}' for k, v in content_slots.items()]
                content_slots_text = '\nBereits freigegebene Texte (diese DIREKT übernehmen, nicht umschreiben):\n' + '\n'.join(lines)

            page_name = briefing_data.get('page_name') or 'Startseite'
            zweck     = briefing_data.get('zweck', '')
            keyword   = briefing_data.get('ziel_keyword', '')
            cta_text  = briefing_data.get('cta_text', '')

            page_context = f'\nZielseite: {page_name}'
            if zweck:    page_context += f'\nSeitenzweck: {zweck}'
            if keyword:  page_context += f'\nZiel-Keyword (SEO): {keyword}'
            if cta_text: page_context += f'\nGewünschter CTA-Text: {cta_text}'

            # ── Inject audit/pagespeed/crawler/briefing context ──────────────
            audit_score   = briefing_data.get('audit_score')
            audit_probs   = briefing_data.get('audit_problems') or []
            ps_mobile     = briefing_data.get('pagespeed_mobile')
            crawler_titles = briefing_data.get('crawler_titles') or []
            b_usp         = briefing_data.get('briefing_usp') or briefing_data.get('usp', '')
            b_leistungen  = briefing_data.get('briefing_leistungen', '')
            b_zielgruppe  = briefing_data.get('briefing_zielgruppe') or briefing_data.get('target_audience', '')

            if audit_score:
                page_context += f'\nAktueller Website-Score: {audit_score}/100'
            if audit_probs:
                page_context += f'\nTop-Probleme der aktuellen Website: {", ".join(str(p) for p in audit_probs[:3])}'
            if ps_mobile:
                page_context += f'\nPageSpeed Mobil: {ps_mobile}/100'
            if crawler_titles:
                page_context += f'\nAktuell vorhandene Seiten: {", ".join(crawler_titles)}'
            if b_usp:
                page_context += f'\nUSP des Betriebs: {b_usp}'
            if b_zielgruppe:
                page_context += f'\nZielgruppe: {b_zielgruppe}'
            if b_leistungen and not briefing_data.get('services'):
                page_context += f'\nLeistungen (Briefing): {b_leistungen}'

            # ── Brand design context ─────────────────────────────────────────
            brand_primary   = briefing_data.get('brand_primary_color')
            brand_secondary = briefing_data.get('brand_secondary_color')
            brand_font      = briefing_data.get('brand_font_primary')
            brand_style     = briefing_data.get('brand_design_style')
            if brand_primary:
                page_context += f'\nPrimärfarbe der Marke: {brand_primary}'
            if brand_secondary:
                page_context += f'\nSekundärfarbe der Marke: {brand_secondary}'
            if brand_font:
                page_context += f'\nSchriftart: {brand_font}'
            if brand_style:
                page_context += f'\nDesignstil: {brand_style}'
            if brand_primary or brand_secondary:
                page_context += '\nBitte den generierten HTML-Entwurf an diese Markenfarben anpassen.'

            system_prompt = """Du bist ein Texter für KOMPAGNON, spezialisiert auf deutsche Handwerksbetriebe.
Schreibe konvertierungsstarke, authentische Website-Texte.

WICHTIG:
- Antworte ausschließlich als valides JSON ohne Markdown-Wrapper
- Ton: vertrauenswürdig, bodenständig, kompetent — kein Marketing-Speak
- Integriere den Ortsnamen natürlich in die Texte
- FAQ-Antworten müssen kurz, faktisch und von KI-Suchmaschinen zitierfähig sein
- hero_headline: max. 8 Wörter, Action-focused, enthält Ziel-Keyword wenn vorhanden
- hero_subline: 1 Satz, Nutzen-fokussiert
- about_text: 150 Wörter, Ich-Perspektive ("Wir sind...", "Wir machen...")
- service_texts: Für jede Leistung 80 Wörter, fokussiert auf Vorteile
- faq_items: Mindestens 5, häufige Fragen aus Sicht der Zielgruppe
- meta_titles: max. 60 Zeichen, enthält Ziel-Keyword wenn vorhanden
- meta_descriptions: max. 160 Zeichen
- local_cta: nutze den angegebenen CTA-Text wenn vorhanden, sonst regionaler CTA mit Ortsnamen
- Bereits freigegebene Texte IMMER unverändert in das Ergebnis übernehmen"""

            user_message = f"""
Erstelle Website-Texte für diesen Betrieb:

Betrieb: {briefing_data.get('company_name', 'Unbekannt')}
Gewerk: {briefing_data.get('trade', 'Handwerk')}
Stadt: {briefing_data.get('city', 'Lokation')}
USP: {briefing_data.get('usp', 'Keine Angabe')}
Leistungen: {', '.join(briefing_data.get('services', []) or [])}
Zielgruppe: {briefing_data.get('target_audience', 'Lokale Kunden')}
Team: {briefing_data.get('team_info', 'Professionelles Team')}
Betrieb seit: {briefing_data.get('years_in_business', 0)} Jahren
Zertifikate: {', '.join(briefing_data.get('awards_or_certifications', []) or [])}{page_context}{content_slots_text}

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
                timeout=55.0,
            )

            response_text = message.content[0].text.strip() if message.content else ""
            if not response_text:
                return {"error": "Leere Antwort von der KI — bitte erneut versuchen."}

            # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                # remove first line (```json or ```) and last line (```)
                inner = [l for l in lines[1:] if l.strip() != "```"]
                response_text = "\n".join(inner).strip()

            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            return {"error": f"KI-Antwort konnte nicht verarbeitet werden (kein gültiges JSON). Bitte erneut versuchen."}
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
