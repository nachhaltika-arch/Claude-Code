"""
GEO/GAIO Optimizer — analysiert Kundenseiten auf KI-Sichtbarkeit.

GEO = Generative Engine Optimization
GAIO = Generative AI Indexing Optimization

Prueft ob eine Website von KI-Systemen (ChatGPT, Perplexity, Google AI)
korrekt verstanden und als vertrauenswuerdig eingestuft wird.
"""

import logging
import json
import re
import httpx

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class GeoOptimizerAgent:
    def __init__(self, api_key: str):
        if Anthropic is None:
            raise RuntimeError("anthropic SDK nicht installiert")
        self.client = Anthropic(api_key=api_key, max_retries=0, timeout=30.0)

    # ── 1. Technische Checks ──────────────────────────────────────

    async def _check_llms_txt(self, website_url: str) -> dict:
        base_url = website_url.rstrip("/")
        url = f"{base_url}/llms.txt"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    content = resp.text[:2000]
                    has_title = "# " in content
                    has_description = len(content) > 50
                    return {
                        "exists": True,
                        "score": 100 if (has_title and has_description) else 60,
                        "content_preview": content[:200],
                        "issues": [] if (has_title and has_description) else ["llms.txt vorhanden aber unvollstaendig"],
                    }
                return {"exists": False, "score": 0, "issues": ["llms.txt fehlt — KI-Systeme erhalten keine Orientierung"]}
        except Exception as e:
            logger.warning("llms.txt check failed for %s: %s", website_url, e)
            return {"exists": False, "score": 0, "issues": [f"llms.txt nicht erreichbar: {str(e)[:100]}"]}

    async def _check_robots_ai(self, website_url: str) -> dict:
        base_url = website_url.rstrip("/")
        url = f"{base_url}/robots.txt"
        blocked_bots = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return {"ai_friendly": True, "score": 80, "blocked_bots": [], "issues": ["robots.txt nicht gefunden (KI-freundlich)"]}
                content = resp.text
                ai_bots = ["GPTBot", "PerplexityBot", "ClaudeBot", "anthropic-ai", "cohere-ai", "Google-Extended"]
                lines = content.split("\n")
                for bot in ai_bots:
                    current_agent = None
                    for line in lines:
                        if line.lower().startswith("user-agent:"):
                            current_agent = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("disallow:") and current_agent in (bot, "*"):
                            disallow_path = line.split(":", 1)[1].strip()
                            if disallow_path in ("/", "/*"):
                                blocked_bots.append(bot)
                                break
                blocked_bots = list(set(blocked_bots))
                is_ai_friendly = len(blocked_bots) == 0
                return {
                    "ai_friendly": is_ai_friendly,
                    "score": 100 if is_ai_friendly else max(0, 100 - len(blocked_bots) * 25),
                    "blocked_bots": blocked_bots,
                    "issues": [f"KI-Bot blockiert: {b}" for b in blocked_bots] if blocked_bots else [],
                }
        except Exception as e:
            logger.warning("robots.txt AI check failed: %s", e)
            return {"ai_friendly": True, "score": 70, "blocked_bots": [], "issues": [f"robots.txt nicht pruefbar: {str(e)[:100]}"]}

    async def _check_structured_data(self, website_url: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(website_url)
                if resp.status_code != 200:
                    return {"has_local_business": False, "score": 0, "schema_types": [], "issues": ["Website nicht erreichbar"]}
                html = resp.text
                schema_matches = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
                schema_types = list(set(schema_matches))
                has_local_business = "LocalBusiness" in schema_types or "HomeAndConstructionBusiness" in schema_types
                has_faq = "FAQPage" in schema_types
                has_service = "Service" in schema_types
                score = 0
                if has_local_business:
                    score += 60
                if has_faq:
                    score += 20
                if has_service:
                    score += 20
                issues = []
                if not has_local_business:
                    issues.append("schema.org LocalBusiness fehlt — KI kann Betrieb nicht einordnen")
                if not has_faq:
                    issues.append("FAQPage Schema fehlt — verpasste Chance fuer KI-Antworten")
                return {
                    "has_local_business": has_local_business,
                    "score": score,
                    "schema_types": schema_types,
                    "issues": issues,
                }
        except Exception as e:
            logger.warning("Structured data check failed: %s", e)
            return {"has_local_business": False, "score": 0, "schema_types": [], "issues": [str(e)[:100]]}

    # ── 2. KI-Inhaltsanalyse ──────────────────────────────────────

    def _analyze_content_with_ai(self, website_text: str, gewerk: str, city: str) -> dict:
        prompt = f"""Du bist ein GEO/GAIO-Experte (Generative Engine Optimization).
Analysiere diesen Website-Content eines {gewerk}-Betriebs aus {city}.

Pruefe:
1. Semantische Tiefe: Werden Fachbegriffe des Gewerks korrekt und umfangreich verwendet?
2. Lokale Signale: Werden Stadt, Region, Stadtteile, lokale Bezuege genannt?
3. Autoritaetssignale: Erfahrungsjahre, Zertifikate, Innungsmitgliedschaft, Bewertungen?
4. KI-zitierbarkeit: Sind Aussagen praezise, faktenbasiert und gut strukturiert?
5. FAQ-Potenzial: Werden haeufige Kundenfragen beantwortet?

Website-Content (erste 3000 Zeichen):
{website_text[:3000]}

Antworte NUR als JSON:
{{
  "content_depth_score": 0,
  "local_signal_score": 0,
  "authority_score": 0,
  "ai_citable_score": 0,
  "faq_potential_score": 0,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "ai_summary": "2-Satz Gesamtbewertung auf Deutsch"
}}"""
        try:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception as e:
            logger.error("AI content analysis failed: %s", e)
            return {
                "content_depth_score": 50,
                "local_signal_score": 50,
                "authority_score": 50,
                "ai_citable_score": 50,
                "faq_potential_score": 50,
                "strengths": ["Analyse nicht moeglich"],
                "weaknesses": ["KI-Analyse fehlgeschlagen"],
                "ai_summary": "Automatische Analyse fehlgeschlagen — manuelle Pruefung empfohlen.",
            }

    # ── 3. Haupt-Analyse ──────────────────────────────────────────

    async def analyze(self, website_url: str, gewerk: str, city: str, website_text: str = "") -> dict:
        llms_result = await self._check_llms_txt(website_url)
        robots_result = await self._check_robots_ai(website_url)
        schema_result = await self._check_structured_data(website_url)

        ai_result = {}
        if website_text:
            ai_result = self._analyze_content_with_ai(website_text, gewerk, city)

        llms_score = llms_result.get("score", 0)
        robots_score = robots_result.get("score", 0)
        schema_score = schema_result.get("score", 0)
        content_score = ai_result.get("content_depth_score", 50)
        local_score = ai_result.get("local_signal_score", 50)

        geo_total = int(
            llms_score * 0.20 +
            robots_score * 0.20 +
            schema_score * 0.25 +
            content_score * 0.20 +
            local_score * 0.15
        )

        recommendations = []
        if not llms_result.get("exists"):
            recommendations.append({
                "prioritaet": "hoch",
                "titel": "llms.txt anlegen",
                "beschreibung": "Erstelle /llms.txt mit Betriebsbeschreibung, Leistungen und Kontakt. KI-Systeme bevorzugen Websites mit llms.txt.",
                "aufwand": "1 Stunde",
            })
        if robots_result.get("blocked_bots"):
            recommendations.append({
                "prioritaet": "hoch",
                "titel": "KI-Bots in robots.txt freigeben",
                "beschreibung": f"Entferne Disallow-Regeln fuer: {', '.join(robots_result['blocked_bots'])}",
                "aufwand": "15 Minuten",
            })
        if not schema_result.get("has_local_business"):
            recommendations.append({
                "prioritaet": "hoch",
                "titel": "schema.org LocalBusiness einbauen",
                "beschreibung": "Strukturierte Daten helfen KI-Systemen den Betrieb korrekt einzuordnen (Name, Adresse, Oeffnungszeiten, Gewerk).",
                "aufwand": "2 Stunden",
            })

        return {
            "geo_score_total": geo_total,
            "llms_txt_score": llms_score,
            "robots_ai_score": robots_score,
            "structured_data_score": schema_score,
            "content_depth_score": content_score,
            "local_signal_score": local_score,
            "raw_checks": {
                "llms_txt": llms_result,
                "robots_ai": robots_result,
                "structured_data": schema_result,
                "ai_content": ai_result,
            },
            "recommendations": recommendations,
        }
