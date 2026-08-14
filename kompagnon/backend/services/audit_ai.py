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

from services.audit_criteria import ai_criteria, ist_anwendbar
from services.audit_industry_map import klasse_fuer_branche
from services.audit_industry_profiles import rubric_fuer_prompt

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover — Abhängigkeit fehlt nur in Minimal-Setups
    Anthropic = None

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_RECOGNITION_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4000
ERKENNUNGS_TOKENS = 300
REQUEST_TIMEOUT = 90.0
PAGE_TEXT_LIMIT = 6000

SYSTEM_PROMPT = """Du bewertest Websites für den KOMPAGNON Homepage Standard.

Die Seite ist bereits eingeordnet. Ihre Branchenklasse und der Maßstab, der
daraus folgt, stehen in der Nachricht — halte dich daran. Steht dort kein
Maßstab, steckt hinter der Seite kein Betrieb: Dann wirf ihr NICHT vor, was ein
Betrieb hätte — keine fehlenden Leistungsbeschreibungen, kein fehlendes
Einsatzgebiet, keinen fehlenden Preisrahmen. Halte 'ai_summary', 'top_issues'
und 'recommendations' in dem Fall bei dem, was für DIESE Seite gilt —
Gestaltung, Lesbarkeit, Kontrast, Aktualität — und sage im ersten Satz klar,
dass der KOMPAGNON Homepage Standard auf Betriebe zugeschnitten ist und für
diese Seite deshalb nur eingeschränkt aussagt.

Was der Maßstab der Klasse ausdrücklich NICHT erwartet, fehlt nicht. Es kostet
keinen Punkt und gehört in keine Begründung, keine Empfehlung und keinen
Befund. Ein Beratungsberuf ohne Preisangabe ist nicht unvollständig, sondern
berufsrechtlich korrekt.

Du bewertest AUSSCHLIESSLICH die unten aufgeführten Kriterien. Alles andere —
Recht, Sicherheit, Performance, SEO, Barrierefreiheit — wurde bereits technisch
gemessen und ist nicht deine Aufgabe.

MASZSTAB: die Sicht der Kundschaft, die diese Seite gewinnen soll — bei einem
Handwerksbetrieb also Hausbesitzer mit einem konkreten Vorhaben aus dessen
Gewerk, bei anderen Branchen die dort passende Kundschaft. Bewerte nicht aus
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


def erkennungs_modell() -> str:
    """Für die Einordnung reicht das kleine Modell.

    Die Frage ist „was ist das für eine Seite", nicht „wie gut ist sie" — dafür
    das teure Modell zu nehmen, hiesse den Aufpreis für nichts zu zahlen.
    """
    return (os.getenv("AUDIT_RECOGNITION_MODEL", DEFAULT_RECOGNITION_MODEL).strip()
            or DEFAULT_RECOGNITION_MODEL)


def api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def _rubric(klasse: str = "") -> str:
    """Kriterienliste für den Prompt — direkt aus dem Katalog.

    Was für diese Branchenklasse nicht gilt, steht gar nicht erst da. Ein
    Kriterium im Prompt, das später verworfen wird, kostet nur Token und
    verleitet das Modell, es in der Zusammenfassung doch zu bemängeln.
    """
    lines = []
    for crit in ai_criteria():
        if klasse and not ist_anwendbar(crit.key, klasse):
            continue
        lines.append(f"- {crit.key} (0-{crit.max_points}): {crit.label} — {crit.hint}")
    return "\n".join(lines)


def _klassenteil(klasse: str) -> str:
    """Der klassenabhängige Maßstab, wenn es einen gibt."""
    rubric = rubric_fuer_prompt(klasse) if klasse else ""
    return f"{rubric}\n\n" if rubric else ""


def _schema() -> dict:
    """JSON-Schema für die strukturierte Antwort — direkt aus dem Katalog.

    Ohne numerische Grenzen: die API unterstützt minimum/maximum nicht.
    Die Begrenzung auf die Maximalpunktzahl passiert beim Eintragen im Scoring.
    """
    properties = {c.key: {"type": "integer"} for c in ai_criteria()}
    properties.update({
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


def _user_content(facts: dict, summary: dict, screenshot_b64: Optional[str],
                  klasse: str = "") -> list:
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
            f"ZU BEWERTENDE KRITERIEN:\n{_rubric(klasse)}\n\n"
            f"{_klassenteil(klasse)}"
            f"SEITENTEXT DER STARTSEITE:\n{(facts.get('page_text') or '')[:PAGE_TEXT_LIMIT]}\n\n"
            "Zusätzlich: 'begruendung' (2-3 Sätze zu deiner Design- und "
            "Conversion-Bewertung), 'ai_summary' (3-5 Sätze in einfacher Sprache "
            "für den Betriebsinhaber), 'top_issues' (die 3 größten konkreten "
            "Probleme), 'recommendations' (3-5 konkrete nächste Schritte)."
        ),
    })
    return content


ERKENNUNGS_PROMPT = """Du ordnest eine Website ein. Du bewertest sie nicht.

Zwei Angaben, mehr nicht:

- 'branche': Was ist das für eine Seite? Nenne das Gewerk oder die Branche so
  konkret wie erkennbar — „Dachdecker", „Heizung und Sanitär",
  „Steuerberatung", „Restaurant" — oder, wenn dahinter kein Betrieb steckt,
  was es sonst ist: „politischer Kandidat", „Verein", „Blog", „private Seite".
- 'betriebsseite': true, wenn dahinter ein Betrieb oder eine Organisation
  steht, die über diese Website Kunden für ihre Leistungen gewinnen will.
  false sonst.

Richte dich nach der Seite selbst. Angaben aus unseren Stammdaten können
falsch oder leer sein."""

ERKENNUNGS_SCHEMA = {
    "type": "object",
    "properties": {
        "branche": {"type": "string"},
        "betriebsseite": {"type": "boolean"},
    },
    "required": ["branche", "betriebsseite"],
    "additionalProperties": False,
}


def _ruf_modell(*, systemprompt: str, inhalt, schema: dict, max_tokens: int,
                modell: str) -> Optional[dict]:
    """Ein Aufruf beim Modell. Getrennt, damit der Test ihn ersetzen kann.

    Gibt None zurück, wenn nichts Brauchbares kam — nie einen Ersatzwert.
    """
    if Anthropic is None:
        logger.warning("KI übersprungen: anthropic-Paket nicht installiert")
        return None
    if not api_key():
        logger.warning("KI übersprungen: ANTHROPIC_API_KEY nicht gesetzt")
        return None

    try:
        client = Anthropic(api_key=api_key(), max_retries=1, timeout=REQUEST_TIMEOUT)
        response = client.messages.create(
            model=modell,
            max_tokens=max_tokens,
            system=systemprompt,
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": schema},
            },
            messages=[{"role": "user", "content": inhalt}],
        )
    except Exception as e:  # noqa: BLE001 — darf das Audit nie abbrechen
        logger.warning(f"KI-Aufruf fehlgeschlagen: {type(e).__name__}: {e}")
        return None

    if response.stop_reason == "refusal":
        logger.warning("KI-Aufruf abgelehnt (refusal)")
        return None

    text = next((b.text for b in response.content if b.type == "text"), "")
    if not text:
        logger.warning("KI-Aufruf lieferte keinen Text")
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Bei output_config.format sollte das nicht vorkommen — wenn doch,
        # lieber nichts eintragen als geraten.
        logger.warning(f"KI-Antwort nicht parsebar trotz Schema: {e}")
        return None


def _erkennungs_inhalt(facts: dict) -> str:
    """Für die Einordnung reicht Text — ein Bild kostet ein Vielfaches."""
    return (
        f"Stammdaten (können falsch sein): Betrieb "
        f"{facts.get('company_name') or '—'}, Gewerk "
        f"{facts.get('trade') or '—'}, Ort {facts.get('city') or '—'}, "
        f"{facts.get('url') or '—'}\n\n"
        f"SEITENTEXT DER STARTSEITE:\n"
        f"{(facts.get('page_text') or '')[:PAGE_TEXT_LIMIT]}"
    )


def evaluate(
    facts: dict,
    summary: Optional[dict] = None,
    screenshot_b64: Optional[str] = None,
) -> dict:
    """Ordnet die Seite ein und bewertet sie gegen den Maßstab ihrer Klasse.

    Zwei Aufrufe, und die Reihenfolge ist der Kern: Der Maßstab hängt an der
    Branchenklasse, die Klasse an der Erkennung. Beides in einem Aufruf hiesse,
    dem Modell die Wahl seines eigenen Maßstabs zu überlassen — dann liefe
    dieselbe Website an zwei Tagen gegen zwei Maßstäbe, und ein Standard, der
    das tut, ist keiner (Bewertungslogik 2026.2, § 2.3).

    Schlägt die Erkennung fehl, wird gar nicht bewertet: Ohne Klasse bliebe nur
    der alte feste Maßstab, und der war der Grund für den Umbau. Schlägt nur
    die Bewertung fehl, bleibt die Einordnung erhalten — sie erklärt dem Leser
    immerhin den Rahmen.
    """
    erkennung = _ruf_modell(
        systemprompt=ERKENNUNGS_PROMPT,
        inhalt=_erkennungs_inhalt(facts),
        schema=ERKENNUNGS_SCHEMA,
        max_tokens=ERKENNUNGS_TOKENS,
        modell=erkennungs_modell(),
    )
    if not erkennung:
        logger.warning("Einordnung fehlgeschlagen — keine Bewertung ohne Maßstab")
        return {}

    branche = str(erkennung.get("branche") or "")
    betriebsseite = bool(erkennung.get("betriebsseite"))
    zuordnung = klasse_fuer_branche(branche, betriebsseite)

    grundlage = {
        "branche": branche,
        "betriebsseite": betriebsseite,
        "branchenklasse": zuordnung.klasse,
        "branchenklasse_quelle": zuordnung.quelle,
    }

    bewertung = _ruf_modell(
        systemprompt=SYSTEM_PROMPT,
        inhalt=_user_content(facts, summary or {}, screenshot_b64, zuordnung.klasse),
        schema=_schema(),
        max_tokens=MAX_TOKENS,
        modell=model_name(),
    )
    if not bewertung:
        return grundlage

    return {**grundlage, **bewertung}
