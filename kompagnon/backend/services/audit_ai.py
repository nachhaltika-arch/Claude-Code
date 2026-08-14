"""
KI-Bewertung der subjektiven Audit-Kriterien.

Bewertet ausschließlich das, was sich von außen nicht hart messen lässt:
Design, Conversion und Textqualität. Alle übrigen Kriterien kommen
deterministisch aus ``audit_collectors`` — die KI bekommt sie gar nicht erst
zu Gesicht, damit sie nicht Werte rät, die längst gemessen sind.

Der Altcode ließ die KI alle 33 Kriterien schätzen und fiel bei jedem Fehler auf
feste Konstanten zurück. Hier gilt: schlägt die Bewertung fehl, werden die
betroffenen Kriterien als 'nicht erhoben' geführt und aus dem Score genommen.

Schema und Prompt werden aus dem Kriterienkatalog erzeugt — ein neues
KI-Kriterium im Katalog landet automatisch in beidem.
"""
import json
import logging
import os
from typing import Optional

from services.audit_criteria import ai_criteria

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover — Abhängigkeit fehlt nur in Minimal-Setups
    Anthropic = None

DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 4000
REQUEST_TIMEOUT = 90.0
PAGE_TEXT_LIMIT = 6000

SYSTEM_PROMPT = """Du bewertest Websites für den KOMPAGNON Homepage Standard.

ERST ERKENNEN, DANN BEWERTEN. Zwei Felder gehören in jede Antwort:

- 'branche': Was ist das für eine Seite? Nenne das Gewerk oder die Branche so
  konkret wie erkennbar — „Dachdecker", „Heizung und Sanitär", „Steuerberatung",
  „Restaurant" — oder, wenn dahinter kein Betrieb steckt, was es sonst ist:
  „politischer Kandidat", „Verein", „Blog", „private Seite", „Baustellenseite".
- 'betriebsseite': true, wenn dahinter ein Betrieb oder eine Organisation steht,
  die über diese Website Kunden für ihre Leistungen gewinnen will. false sonst.

Bei 'betriebsseite': false wirf der Seite NICHT vor, was ein Betrieb hätte:
keine fehlenden Leistungsbeschreibungen, kein fehlendes Einsatzgebiet, kein
fehlender Preisrahmen. Diese Kriterien werden dann verworfen und zählen nicht.
Halte 'ai_summary', 'top_issues' und 'recommendations' in diesem Fall bei dem,
was für DIESE Seite gilt — Gestaltung, Lesbarkeit, Kontrast, Aktualität — und
sage im ersten Satz klar, dass der KOMPAGNON Homepage Standard auf Betriebe
zugeschnitten ist und für diese Seite deshalb nur eingeschränkt aussagt.

Du bewertest AUSSCHLIESSLICH die unten aufgeführten Kriterien. Alles andere —
Recht, Sicherheit, Performance, SEO, Barrierefreiheit — wurde bereits technisch
gemessen und ist nicht deine Aufgabe.

MASZSTAB: die Sicht der Kundschaft, die diese Seite gewinnen soll — bei einem
Handwerksbetrieb also Hausbesitzer mit einem konkreten Vorhaben aus dessen
Gewerk, bei anderen Branchen die dort passende Kundschaft. Leite den Maßstab aus
der erkannten Branche ab, nicht aus einer festen Liste, und bewerte nicht aus
Sicht eines Designers.

Sei streng, aber begründet. Vergib die volle Punktzahl nur, wenn es dafür
sichtbare Belege gibt. Wenn du etwas nicht beurteilen kannst, vergib 0 Punkte
und benenne im Feld 'begruendung', was fehlt.

TON DER TEXTE: Der Betriebsinhaber liest das über seine eigene Arbeit. Sei in
der Sache klar und in der Wortwahl sachlich — beschreibe, was fehlt oder
besser geht, nicht wie schlecht etwas ist. Abwertende Urteile über Texte und
Gestaltung sind tabu: nicht „floskelhaft", „Worthülsen", „nichtssagend",
„lieblos" oder „amateurhaft". Sag stattdessen, was konkret fehlt — etwa „zu
allgemein formuliert", „nicht konkret genug", „zu geläufig, um im Gedächtnis
zu bleiben", „ohne individuellen Bezug zum Betrieb". Statt „schlechte Bilder"
lieber „Bilder ohne Bezug zum eigenen Betrieb". Jede Kritik nennt den
konkreten Punkt und möglichst den Nutzen, der dadurch verloren geht."""


def model_name() -> str:
    return os.getenv("AUDIT_AI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def _rubric() -> str:
    """Kriterienliste für den Prompt — direkt aus dem Katalog."""
    lines = []
    for crit in ai_criteria():
        lines.append(f"- {crit.key} (0-{crit.max_points}): {crit.label} — {crit.hint}")
    return "\n".join(lines)


def _schema() -> dict:
    """JSON-Schema für die strukturierte Antwort — direkt aus dem Katalog.

    Ohne numerische Grenzen: die API unterstützt minimum/maximum nicht.
    Die Begrenzung auf die Maximalpunktzahl passiert beim Eintragen im Scoring.
    """
    properties = {c.key: {"type": "integer"} for c in ai_criteria()}
    properties.update({
        # Die Erkennung steht vor der Bewertung: `betriebsseite` entscheidet im
        # Scoring, ob die angebotsbezogenen Kriterien überhaupt gelten.
        "branche": {"type": "string"},
        "betriebsseite": {"type": "boolean"},
        "begruendung": {"type": "string"},
        "ai_summary": {"type": "string"},
        "top_issues": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
    })
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


def _user_content(facts: dict, summary: dict, screenshot_b64: Optional[str]) -> list:
    """Baut die Nachricht: Screenshot zuerst, dann Fakten und Seitentext."""
    content = []

    if screenshot_b64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": screenshot_b64,
            },
        })

    context = {
        "betrieb": facts.get("company_name") or "",
        "gewerk": facts.get("trade") or "",
        "ort": facts.get("city") or "",
        "url": facts.get("url") or "",
        "gemessene_signale": {
            "cta_beispiele": (facts.get("cta") or {}).get("examples", []),
            "vertrauenssignale": {
                k: v for k, v in (facts.get("trust") or {}).items()
                if isinstance(v, bool)
            },
            "leistungsseiten": (facts.get("services") or {}).get("pages", []),
            "wortanzahl_startseite": facts.get("word_count"),
            "bilder_gesamt": (facts.get("images") or {}).get("total"),
        },
    }

    content.append({
        "type": "text",
        "text": (
            f"Bewerte diese Website.\n\n"
            f"KONTEXT:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n\n"
            f"ZU BEWERTENDE KRITERIEN:\n{_rubric()}\n\n"
            f"SEITENTEXT DER STARTSEITE:\n{(facts.get('page_text') or '')[:PAGE_TEXT_LIMIT]}\n\n"
            "Das Gewerk im Kontext stammt aus unseren Stammdaten und kann falsch "
            "oder leer sein — richte dich nach der Seite selbst und korrigiere es "
            "in 'branche', wenn es nicht passt.\n\n"
            "Zusätzlich: 'branche' und 'betriebsseite' (siehe oben), "
            "'begruendung' (2-3 Sätze zu deiner Design- und "
            "Conversion-Bewertung), 'ai_summary' (3-5 Sätze in einfacher Sprache "
            "für den Betriebsinhaber), 'top_issues' (die 3 größten konkreten "
            "Probleme), 'recommendations' (3-5 konkrete nächste Schritte)."
        ),
    })
    return content


def evaluate(
    facts: dict,
    summary: Optional[dict] = None,
    screenshot_b64: Optional[str] = None,
) -> dict:
    """Bewertet die KI-Kriterien. Gibt bei jedem Fehler ein leeres dict zurück.

    Ein leeres Ergebnis führt dazu, dass die betroffenen Kriterien als
    'nicht erhoben' gelten — es werden keine Ersatzwerte erfunden.
    """
    if Anthropic is None:
        logger.warning("KI-Bewertung übersprungen: anthropic-Paket nicht installiert")
        return {}
    if not api_key():
        logger.warning("KI-Bewertung übersprungen: ANTHROPIC_API_KEY nicht gesetzt")
        return {}

    try:
        client = Anthropic(api_key=api_key(), max_retries=1, timeout=REQUEST_TIMEOUT)
        response = client.messages.create(
            model=model_name(),
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": _schema()},
            },
            messages=[{
                "role": "user",
                "content": _user_content(facts, summary or {}, screenshot_b64),
            }],
        )
    except Exception as e:  # noqa: BLE001 — Bewertung darf das Audit nie abbrechen
        logger.warning(f"KI-Bewertung fehlgeschlagen: {type(e).__name__}: {e}")
        return {}

    if response.stop_reason == "refusal":
        logger.warning("KI-Bewertung abgelehnt (refusal) — Kriterien bleiben nicht erhoben")
        return {}

    text = next((b.text for b in response.content if b.type == "text"), "")
    if not text:
        logger.warning("KI-Bewertung lieferte keinen Text")
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Bei output_config.format sollte das nicht vorkommen — wenn doch,
        # lieber nichts eintragen als geraten.
        logger.warning(f"KI-Antwort nicht parsebar trotz Schema: {e}")
        return {}
