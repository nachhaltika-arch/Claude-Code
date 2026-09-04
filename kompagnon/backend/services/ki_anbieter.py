"""Die KI-Systeme, die wir nach einem Betrieb fragen koennen (L-58 b).

**Warum ein Register und nicht drei Aufrufe.** GEO verkauft die Aussage „So
sichtbar sind Sie in KI-Systemen". Bis zum 22.08.2026 gab es hier genau einen
Zugang — `ANTHROPIC_API_KEY`. Ein Claude-Ergebnis als Aussage ueber ChatGPT
auszugeben waere eine Behauptung ueber ein System, das wir nie gefragt haben.

**Die Regel ist die aus D1** (Audit, 11.08.2026): Ohne PageSpeed-Schluessel
erfand das Audit Zahlen. Seitdem gilt „nicht erhoben" als eigener Zustand, der
benannt wird und aus der Wertung faellt. Hier genauso: Ein Anbieter ohne
Schluessel wird **ausgewiesen**, niemals geraten und niemals als „kennt den
Betrieb nicht" gezaehlt.

**Stand der Schnittstellen am 22.08.2026** — nachgeschlagen, nicht erinnert:

    Claude       anthropic-SDK, Werkzeug `web_search_20260209`
    ChatGPT      POST https://api.openai.com/v1/responses
                 `tools:[{"type":"web_search"}]`, Modell `gpt-5.6`
    Perplexity   POST https://api.perplexity.ai/v1/agent  (Agent API)
                 Die alte Sonar-Chat-Completions-Form wird **bis zum
                 27.09.2026** unterstuetzt und danach abgeschaltet.
    Google AI    POST https://generativelanguage.googleapis.com/v1beta/interactions
                 Schluessel im Kopf `x-goog-api-key`, Werkzeug
                 `{"type": "google_search"}`, Modell `gemini-3.7-flash`.
                 Nachgeschlagen am 25.08.2026. Die Quellen stehen als
                 `url_citation` im Textblock, nicht in `groundingMetadata` —
                 die aeltere `generateContent`-Form wird trotzdem gelesen.

**Was daran ungeprueft ist, und das ehrlich:** Fuer ChatGPT und Perplexity
liegt hier kein Schluessel. Die Anfrageform stammt aus der Herstellerdoku, die
Antwortform ist **nicht am lebenden Dienst** nachgestellt. Deshalb lesen
`lies_openai_antwort` und `lies_perplexity_antwort` tolerant: Sie kennen
mehrere Formen, greifen nie ins Leere und liefern lieber nichts als Unsinn.
Der erste echte Lauf zeigt, ob sie passen — er zeigt es an einem leeren
Ergebnis, nicht an einem falschen.
"""
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

#: Zeitgrenze je Frage. Eine Websuche dauert; ewig darf sie nicht dauern.
#:
#: **90 statt 45 Sekunden seit dem 31.08.2026, und die Zahl ist gemessen.**
#: Perplexitys Agent API fuehrt mehrere Suchen hintereinander aus und brauchte
#: in drei echten Laeufen 16,8 s, 14,6 s und 23,7 s — einzeln bequem unter 45.
#: Im Sammellauf laufen vier Anbieter gleichzeitig, und dort schlug die Grenze
#: zu. Dieselbe Lehre wie bei `PSI_TIMEOUT` (L-126): Zwischen Normalfall und
#: Grenze muss Spielraum liegen, sonst sieht ein Abbruch aus wie „nicht
#: erhoben" statt wie „zu frueh abgebrochen".
ZEITGRENZE = 90.0

#: Antwortlaenge je Frage. Es geht um die Nennung, nicht um einen Aufsatz.
MAX_TOKENS = 900


def _schluessel(env_name: str) -> str:
    """Der Wert der Umgebungsvariable — leer heisst nicht gesetzt.

    Render legt beim Anlegen eines Feldes eine leere Variable an. Ohne diese
    Pruefung gilt ein leeres Feld als konfiguriert, und der Lauf scheitert
    spaeter mit einem Zugangsfehler statt sauber „nicht erhoben" zu melden.
    """
    return (os.getenv(env_name) or "").strip()


# ── Antworten lesen ──────────────────────────────────────────────────

def _urls(eintraege) -> List[str]:
    """Adressen aus einer Liste, die auch Zeichenketten enthalten darf."""
    heraus = []
    for e in eintraege or []:
        if isinstance(e, str):
            heraus.append(e)
        elif isinstance(e, dict) and e.get("url"):
            heraus.append(e["url"])
    return heraus


def lies_openai_antwort(roh: dict) -> Tuple[str, List[str]]:
    """Text und Quellen aus einer Antwort der Responses API.

    Zwei Quellenwege, beide werden genommen: die Zitate am Textblock
    (`annotations` mit `url_citation`) und die vollstaendige Liste dessen, was
    die Suche herangezogen hat (`web_search_call.action.sources`). Die zweite
    ist umfassender — ein Betrieb kann in den Quellen stehen, ohne im Text
    zitiert zu werden.
    """
    if not isinstance(roh, dict):
        return "", []

    text_teile: List[str] = []
    belege: List[str] = []

    direkt = roh.get("output_text")
    if isinstance(direkt, str) and direkt.strip():
        text_teile.append(direkt.strip())

    for eintrag in roh.get("output") or []:
        if not isinstance(eintrag, dict):
            continue

        if eintrag.get("type") == "web_search_call":
            belege.extend(_urls((eintrag.get("action") or {}).get("sources")))
            continue

        for block in eintrag.get("content") or []:
            if not isinstance(block, dict):
                continue
            stueck = block.get("text")
            if isinstance(stueck, str) and stueck.strip() and not text_teile:
                text_teile.append(stueck.strip())
            for anmerkung in block.get("annotations") or []:
                if isinstance(anmerkung, dict) and anmerkung.get("url"):
                    belege.append(anmerkung["url"])

    return "\n".join(text_teile), list(dict.fromkeys(belege))


def lies_perplexity_antwort(roh: dict) -> Tuple[str, List[str]]:
    """Text und Quellen — Agent API, Responses-Form und die auslaufende Sonar-Form.

    **Am 31.08.2026 am lebenden Dienst nachgestellt, und die Vermutung von
    damals war falsch.** Bis heute suchte diese Funktion ein `output_text`
    ganz oben, sonst `choices[].message.content`, und die Quellen unter
    `search_results` oder `citations` — alles aus der Herstellerdoku
    abgeleitet, nie gemessen. Die Agent API antwortet aber in der
    **Responses-Form**: `output` ist eine **Liste** von Teilen, der Text
    steckt in `output[type=message].content[type=output_text].text`, und die
    Quellen stehen in eigenen Teilen mit `type: "search_results"`.

    **Der Aufruf lief dabei durch — Status 200, kein Fehler.** Das Ergebnis
    war lediglich leer, und ein leeres Ergebnis sieht im Bericht aus wie
    „kennt den Betrieb nicht". Genau davor warnt der Kopftext dieses Moduls
    seit dem 22.08.: Der erste echte Lauf zeigt es an einem leeren Ergebnis,
    nicht an einem falschen. Er hat es gezeigt.

    **Die alten Formen bleiben stehen** — Sonar wird bis zum 27.09.2026
    unterstuetzt (L-81), und ein Schluessel kann auf beides zeigen.
    """
    if not isinstance(roh, dict):
        return "", []

    text = ""
    belege: List[str] = []

    # ── Agent API, Responses-Form (gemessen am 31.08.2026) ──
    for teil in roh.get("output") or []:
        if not isinstance(teil, dict):
            continue
        art = teil.get("type")
        if art == "search_results":
            belege.extend(_urls(teil.get("results")))
            continue
        if art != "message":
            continue
        for block in teil.get("content") or []:
            if not isinstance(block, dict):
                continue
            stueck = block.get("text")
            if isinstance(stueck, str) and stueck.strip() and not text:
                text = stueck.strip()
            # Zitate am Textblock gab es im gemessenen Lauf nicht — sie sind
            # in der Responses-Form aber vorgesehen, und ein Beleg, den man
            # nicht liest, fehlt spaeter im Bericht.
            belege.extend(_urls(block.get("annotations")))

    # ── aeltere und einfachere Formen ──
    if not text:
        direkt = roh.get("output_text")
        if isinstance(direkt, str) and direkt.strip():
            text = direkt.strip()
    if not text:
        for wahl in roh.get("choices") or []:
            inhalt = (wahl or {}).get("message", {}).get("content")
            if isinstance(inhalt, str) and inhalt.strip():
                text = inhalt.strip()
                break

    belege += _urls(roh.get("search_results")) + _urls(roh.get("citations"))
    return text, list(dict.fromkeys(belege))


def lies_gemini_antwort(roh: dict) -> Tuple[str, List[str]]:
    """Text und Quellen aus einer Antwort der Interactions API.

    **Nachgeschlagen am 25.08.2026**, nicht erinnert: Die Antwort ist eine
    Folge von `steps`. Der Schritt `model_output` traegt den `content`, und
    die Quellen stehen als `annotations` vom Typ `url_citation` **im
    Textblock** — nicht in einem eigenen `groundingMetadata`, wie es die
    aeltere `generateContent`-Form tat.

    **Die alte Form wird trotzdem gelesen.** Ein Schluessel, der heute angelegt
    wird, kann auf einen Endpunkt zeigen, der noch `candidates` liefert. Wie
    bei Perplexity stehen beide Formen nebeneinander, statt dass ein
    Formwechsel als „kennt den Betrieb nicht" durchgeht.
    """
    if not isinstance(roh, dict):
        return "", []

    text_teile: List[str] = []
    belege: List[str] = []

    def _bloecke(inhalt):
        """`content` ist mal eine Zeichenkette, mal eine Liste von Bloecken."""
        if isinstance(inhalt, str):
            return [{"text": inhalt}]
        if isinstance(inhalt, list):
            return [b for b in inhalt if isinstance(b, dict)]
        if isinstance(inhalt, dict):
            return [inhalt]
        return []

    # Neue Form: steps → model_output → content → annotations
    for schritt in roh.get("steps") or []:
        if not isinstance(schritt, dict):
            continue
        if schritt.get("type") != "model_output":
            continue
        for block in _bloecke(schritt.get("content")):
            stueck = block.get("text")
            if isinstance(stueck, str) and stueck.strip():
                text_teile.append(stueck.strip())
            for anmerkung in block.get("annotations") or []:
                if isinstance(anmerkung, dict) and anmerkung.get("url"):
                    belege.append(anmerkung["url"])

    # Aeltere Form: candidates → content.parts[].text, Quellen im Grounding
    for kandidat in roh.get("candidates") or []:
        if not isinstance(kandidat, dict):
            continue
        for teil in (kandidat.get("content") or {}).get("parts") or []:
            stueck = (teil or {}).get("text")
            if isinstance(stueck, str) and stueck.strip():
                text_teile.append(stueck.strip())
        grounding = kandidat.get("groundingMetadata") or {}
        for stueckchen in grounding.get("groundingChunks") or []:
            netz = (stueckchen or {}).get("web") or {}
            if netz.get("uri"):
                belege.append(netz["uri"])

    return "\n".join(text_teile), list(dict.fromkeys(belege))


# ── Die vier Anbindungen ─────────────────────────────────────────────

async def _frage_claude(frage: str) -> Tuple[str, List[str]]:
    """Claude mit dem serverseitigen Websuche-Werkzeug.

    Ueber `frag_modell`, weil der `anthropic`-Client synchron ist: direkt aus
    einer `async def` aufgerufen haelt er die Ereignisschleife an, der Server
    antwortet in der Zeit gar nicht mehr, und Renders Proxy kappt die laufende
    Anfrage (17.08.2026, drei 503er auf Staging).
    """
    from anthropic import Anthropic

    from services.ki_aufruf import frag_modell

    client = Anthropic(api_key=_schluessel("ANTHROPIC_API_KEY"),
                       max_retries=0, timeout=ZEITGRENZE)
    antwort = await frag_modell(
        client,
        model="claude-opus-5",
        max_tokens=MAX_TOKENS,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}],
        messages=[{"role": "user", "content": frage}],
    )

    text_teile, belege = [], []
    for block in getattr(antwort, "content", None) or []:
        art = getattr(block, "type", "")
        if art == "text":
            text_teile.append(getattr(block, "text", "") or "")
        elif art == "web_search_tool_result":
            # Ein Fehler kommt als Objekt zurueck, ein Erfolg als Liste. Ohne
            # diese Unterscheidung laeuft man ueber die Felder des Fehlers.
            inhalt = getattr(block, "content", None)
            if isinstance(inhalt, list):
                belege.extend(u for u in (getattr(t, "url", None) for t in inhalt) if u)

    return "\n".join(text_teile), list(dict.fromkeys(belege))


async def _frage_openai(frage: str) -> Tuple[str, List[str]]:
    """ChatGPT ueber die Responses API mit eingeschalteter Websuche."""
    async with httpx.AsyncClient(timeout=ZEITGRENZE) as client:
        antwort = await client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {_schluessel('OPENAI_API_KEY')}",
                     "Content-Type": "application/json"},
            json={"model": "gpt-5.6",
                  "tools": [{"type": "web_search"}],
                  "input": frage},
        )
        antwort.raise_for_status()
        return lies_openai_antwort(antwort.json())


async def _frage_perplexity(frage: str) -> Tuple[str, List[str]]:
    """Perplexity ueber die Agent API.

    `preset: "low"` ist die guenstigste Stufe — gefragt wird nach einer
    Nennung, nicht nach einer Recherche.
    """
    async with httpx.AsyncClient(timeout=ZEITGRENZE) as client:
        antwort = await client.post(
            "https://api.perplexity.ai/v1/agent",
            headers={"Authorization": f"Bearer {_schluessel('PERPLEXITY_API_KEY')}",
                     "Content-Type": "application/json"},
            json={"preset": "low", "input": frage},
        )
        antwort.raise_for_status()
        return lies_perplexity_antwort(antwort.json())


async def _frage_gemini(frage: str) -> Tuple[str, List[str]]:
    """Google AI ueber die Interactions API mit eingeschalteter Suche.

    Der Schluessel geht in den Kopf (`x-goog-api-key`) und nicht in die
    Adresse: Eine Adresse mit Schluessel landet in Protokollen, im Verlauf und
    in jeder Fehlermeldung.
    """
    async with httpx.AsyncClient(timeout=ZEITGRENZE) as client:
        antwort = await client.post(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            headers={"x-goog-api-key": _schluessel("GEMINI_API_KEY"),
                     "Content-Type": "application/json"},
            json={"model": "gemini-3.7-flash",
                  "tools": [{"type": "google_search"}],
                  "input": frage},
        )
        antwort.raise_for_status()
        return lies_gemini_antwort(antwort.json())


# ── Das Register ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Anbieter:
    """Ein KI-System, das nach dem Betrieb gefragt werden kann."""

    schluessel: str
    anzeige: str
    env_name: str
    modell: str
    _aufruf: Callable[[str], Any] = field(repr=False)

    def ist_konfiguriert(self) -> bool:
        return bool(_schluessel(self.env_name))

    async def frage_stellen(self, frage: str) -> Tuple[str, List[str]]:
        """Wirft weiter — der Lauf entscheidet, wie ein Ausfall zaehlt."""
        return await self._aufruf(frage)


#: Die Reihenfolge ist die der Marktbedeutung fuer die Kundenfrage
#: „Werde ich gefunden?" — ChatGPT zuerst, weil danach gefragt wird.
ANBIETER: Tuple[Anbieter, ...] = (
    Anbieter("chatgpt", "ChatGPT", "OPENAI_API_KEY", "gpt-5.6", _frage_openai),
    Anbieter("perplexity", "Perplexity", "PERPLEXITY_API_KEY", "sonar (Agent API)",
             _frage_perplexity),
    Anbieter("claude", "Claude", "ANTHROPIC_API_KEY", "claude-opus-5", _frage_claude),
    # Vierter Anbieter seit dem 25.08.2026. Ohne ihn misst der Standard drei
    # Systeme, waehrend der Markt vier nennt — und die Luecke waere ein
    # Verkaufsargument des Wettbewerbs, kein Ergebnis.
    Anbieter("gemini", "Google AI", "GEMINI_API_KEY", "gemini-3.7-flash",
             _frage_gemini),
)


def finde_anbieter(schluessel: str) -> Optional[Anbieter]:
    return next((a for a in ANBIETER if a.schluessel == schluessel), None)


def konfigurierte_anbieter() -> List[Anbieter]:
    """Die Anbieter, die einen Schluessel haben. Kann leer sein."""
    return [a for a in ANBIETER if a.ist_konfiguriert()]


def anbieter_stand() -> List[dict]:
    """Wer ist angebunden, wer fehlt — fuer Diagnose und Bericht.

    Bewusst ohne Schluesselwerte: Diese Liste geht an die Oberflaeche, und
    `/info` hat am 15.08.2026 schon einmal Zugangsdaten preisgegeben.
    """
    return [{"schluessel": a.schluessel, "anzeige": a.anzeige,
             "modell": a.modell, "env_name": a.env_name,
             "konfiguriert": a.ist_konfiguriert()} for a in ANBIETER]
