"""
QA Agent: Evaluate website against checklist and provide go-live recommendation.
"""
import json
import os
from typing import Dict, Optional, List

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class QaAgent:
    """Conduct QA review and provide go-live readiness score."""

    def __init__(self, api_key: Optional[str] = None):
        if not Anthropic:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"

    def conduct_qa(
        self,
        project_id: int,
        checklist_data: Dict,
        test_results: Dict,
    ) -> Dict:
        """
        Conduct QA review based on checklists and test results.

        Args:
            project_id: Project ID
            checklist_data: {
                'completed_items': [str],  # item keys
                'critical_incomplete': [str],  # critical items not done
            }
            test_results: {
                'pagespeed_score': 0-100,
                'link_check_errors': int,
                'ssl_valid': bool,
                'mobile_responsive': bool,
                'impressum_present': bool,
                'dsgvo_compliant': bool,
            }

        Returns:
            {
                'overall_qa_score': 0-100,
                'critical_failures': [str],
                'warnings': [str],
                'passed_items': int,
                'failed_items': int,
                'go_live_recommendation': bool,
                'summary': str (3 sentences for client presentation),
                'detailed_report': str (for internal use),
            }
        """
        try:
            system_prompt = """Du bist ein QA-Ingenieur für KOMPAGNON.
Evaluiere WordPress-Websites gegen strenge Kriterien bevor sie live gehen.

WICHTIG:
- Antworte als valides JSON ohne Markdown-Wrapper
- Sei objektiv und neutral, fokussiere auf faktische Probleme
- Go-Live empfohlen nur wenn: PageSpeed >85, keine kritischen Fehler, DSGVO OK
- critical_failures: Blockers (SSL, Impressum, Datenschutz)
- warnings: Optimierungsbedarf (Performance, Links)
- summary: 3 Sätze für Kundenpräsentation, verständlich, professionell"""

            user_message = f"""
Führe QA-Review für Projekt {project_id} durch:

Checklisten-Status:
{json.dumps(checklist_data, indent=2, ensure_ascii=False)}

Test-Ergebnisse:
{json.dumps(test_results, indent=2, ensure_ascii=False)}

Liefere das Ergebnis als JSON:
{{
    "overall_qa_score": <0-100>,
    "critical_failures": ["Fehler 1", "Fehler 2"],
    "warnings": ["Warnung 1", "Warnung 2"],
    "passed_items": <Anzahl>,
    "failed_items": <Anzahl>,
    "go_live_recommendation": <true/false>,
    "summary": "<3 Sätze für Kundenfreigabe>",
    "detailed_report": "<Längerer Bericht für intern>"
}}"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            response_text = message.content[0].text
            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            return {"error": f"QA evaluation failed: {str(e)}"}

    @staticmethod
    def get_mock_qa(project_id: int) -> Dict:
        """Return mock QA results for testing."""
        return {
            "overall_qa_score": 89,
            "critical_failures": [],
            "warnings": [
                "PageSpeed Score könnte noch optimiert werden (aktuell 82, Ziel 85+)",
                "2 externe Links geben 404-Fehler zurück — bitte überprüfen",
            ],
            "passed_items": 47,
            "failed_items": 2,
            "go_live_recommendation": True,
            "summary": "Die Website erfüllt alle kritischen Anforderungen und kann live gehen. PageSpeed könnte noch leicht optimiert werden, ist aber für Handwerksbetriebe ausreichend. Alle rechtlichen Anforderungen (DSGVO, Impressum, SSL) sind erfüllt.",
            "detailed_report": """QA-Report für Projekt #123

BESTANDENE TESTS:
✓ SSL-Zertifikat gültig und aktiv
✓ Datenschutzerklärung DSGVO-konform vorhanden
✓ Impressum aktuell und vollständig
✓ Mobile Responsive Design funktioniert
✓ Alle Formulare getestet — E-Mail-Verarbeitung OK
✓ Google Search Console verifiziert
✓ Meta-Tags und Descriptions auf allen Seiten
✓ Rich Results validiert (LocalBusiness Schema)

OPTIMIERUNGSBEDARF:
⚠ PageSpeed Score 82 (Ziel 85+)
  - Bilder könnten weiter komprimiert werden
  - Cache-Header könnten optimaler sein

⚠ Link-Check: 2 externe Links geben 404
  - https://example.com/old-page → Weiterleitung nötig oder entfernen
  - https://partner.com/service → Partner kontaktieren oder Link entfernen

EMPFEHLUNGEN:
1. Die 2 fehlerhaften Links vor Go-Live reparieren (5 Min Aufwand)
2. Nach Go-Live weiterbeobachten und PageSpeed optimieren
3. Monitoring einrichten (GA4 funktioniert bereits)

FAZIT: Go-Live freigegeben. Website ist produktionsreif.""",
        }
