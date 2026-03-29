"""
Review Agent: Generate personalized review request emails and phone scripts.
"""
import json
import os
from typing import Dict, Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class ReviewAgent:
    """Generate review requests and sales scripts."""

    def __init__(self, api_key: Optional[str] = None):
        if not Anthropic:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"

    def generate_review_request(
        self,
        customer_name: str,
        company_name: str,
        project_summary: str,
        platform: str = "google",  # google or provenexpert
    ) -> Dict:
        """
        Generate personalized review request for go-live followup.

        Args:
            customer_name: Contact person name
            company_name: Business name
            project_summary: Brief description of work done
            platform: 'google' or 'provenexpert'

        Returns:
            {
                'email_subject': str,
                'email_body': str (150 words, personal, not generic),
                'phone_script': str (bullet points with what to say/avoid),
                'review_link_placeholder': str (e.g., [GOOGLE_REVIEW_LINK]),
            }
        """
        try:
            system_prompt = """Du bist ein Sales-Spezialist für KOMPAGNON.
Generiere persönliche Bewertungsanfragen und Verkaufsskripte.

WICHTIG:
- Antworte als valides JSON ohne Markdown-Wrapper
- E-Mail: max. 150 Wörter, persönlich nicht generisch, deutsche Anrede
- Phone-Script: Bullet Points, konkrete Formulierungen, was sagen/vermeiden
- Tone: Warmherzig, professionell, keine Drängerei — natürlicher Dialog
- Fokus: Zufriedenheit aufbauen, nicht nur Bitte um Bewertung"""

            user_message = f"""
Generiere Bewertungsanfrage für:

Ansprechpartner: {customer_name}
Unternehmen: {company_name}
Projekt: {project_summary}
Plattform: {platform}

Liefere das Ergebnis als JSON:
{{
    "email_subject": "<Betreffzeile>",
    "email_body": "<150 Wörter, persönlich>",
    "phone_script": "<Bullet Points für Telefonat>",
    "review_link_placeholder": "<Placeholder für Review-Link>"
}}"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            response_text = message.content[0].text
            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            return {"error": f"Review request generation failed: {str(e)}"}

    @staticmethod
    def get_mock_review(customer_name: str, company_name: str, platform: str = "google") -> Dict:
        """Return mock review request for testing."""
        return {
            "email_subject": f"Danke, {company_name}! Wie war die Zusammenarbeit?",
            "email_body": f"""Lieber {customer_name},

zwei Wochen ist Ihre neue Website jetzt online — herzlichen Glückwunsch! 🎉

Wir sind überwältigt, wie schnell alles geklappt hat und wie zufrieden Sie mit der Zusammenarbeit waren. Jetzt wollten wir Sie um einen kleinen Gefallen bitten: Falls Ihre Website bereits Anfragen gebracht hat und Sie zufrieden sind, würde es uns riesig freuen, wenn Sie uns eine kurze Bewertung hinterlassen könnten.

Das ist für andere Handwerksbetriebe in {company_name.split()[-1] if ',' in company_name else 'Ihrer Region'} wichtig — echte Erfahrungen von echten Kunden zählen!

{f"[GOOGLE_REVIEW_LINK]" if platform == "google" else "[PROVENEXPERT_REVIEW_LINK]"}

Vielen Dank,
Ihr KOMPAGNON-Team""",
            "phone_script": f"""
• Hallo {customer_name}, hier ist [Name] von KOMPAGNON — kurz zwei Wochen nach dem Go-Live nur schnell durchgerufen wie es läuft?

• [Zuhören — echtes Interesse zeigen]

• Super, genau das wollten wir hören! Die Website funktioniert also gut?

• [Bei Problemen kurz helfen, bei Zufriedenheit weitermachen]

• Wir hätten noch eine kleine Bitte: Falls Sie mit der Website und der Zusammenarbeit zufrieden sind, könnten Sie uns eine kurze Bewertung auf [Google/ProvenExpert] hinterlassen?

• Das hilft anderen Betrieben in Ihrer Branche, uns zu finden. Dauert nur 2 Minuten!

• [Link senden/E-Mail mit Link]

• Vielen Dank! Und: Falls später was nicht läuft — einfach anrufen, wir sind ja da!

---
VERMEIDEN:
❌ "Bitte geben Sie uns eine 5-Sterne-Bewertung"
❌ Bewertung als Bedingung hingestellt
❌ Zu oft nachfragen
❌ Druck aufbauen

ZIEL: Natürlicher Dialog, echte Zufriedenheit, keine Drängerei
""",
            "review_link_placeholder": "[GOOGLE_REVIEW_LINK]" if platform == "google" else "[PROVENEXPERT_LINK]",
        }
