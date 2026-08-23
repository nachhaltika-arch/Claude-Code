"""Bausteine vom Modell erzeugen lassen (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/component_library.py` hatte nach
dem Wireframe-Schnitt noch 1.237 Zeilen, und mehr als die Haelfte davon war
Modellarbeit: Aufforderungen bauen, Antworten lesen, Fehlendes nachbessern,
Pflichtfelder pruefen. Mit dem Verwalten der Bibliothek — anlegen, aendern,
freigeben, loeschen — hat das nichts gemeinsam ausser dem Gegenstand.

Transitiv gemessen samt Modulkonstanten. Geteilt bleiben `_befund` und
`_serialize_component`; sie werden von drueben geholt statt kopiert.

`component_library_wireframe.py` holt seine drei KI-Helfer seit diesem
Schnitt von **hier** — sie sind mitgewandert.
"""
import json
import os
import threading
import uuid
from typing import Optional
# **Mit Rueckfall, wie in `component_library.py`.** Ein direktes
# `from anthropic import Anthropic` haette bei fehlendem Paket den Start
# zerlegt, statt auf `None` zu fallen — der Unterschied faellt erst auf,
# wenn das Paket wirklich fehlt (L-25, 22.08.2026).
try:
    from anthropic import Anthropic
except Exception:  # noqa: BLE001
    Anthropic = None

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from routers.auth_router import require_any_auth, require_innendienst
from services.block_contract import als_text, pruefe, slots_im_markup
from services.block_slots import ergaenze_fehlende_slots
from routers.component_library_daten import _ELEMENT_LABELS, _INDUSTRIES, _LAYOUT_PRESETS, _WIREFRAME_CONSTRAINTS
from routers.component_library import _Abbruch, _component_gen_jobs
from database import Briefing
from database import ComponentLibrary
from database import get_db
import logging

from routers.component_library import (GenerateComponentRequest, GenerateCopyRequest, VariationRequest, _befund, _serialize_component, component_router)

logger = logging.getLogger(__name__)


@component_router.post("/generate")
def generate_component(
    body: GenerateComponentRequest,
    user=Depends(require_any_auth),
):
    """Startet KI-Komponenten-Generierung als Background-Job.

    Returnt sofort {job_id, status: 'running'}. Frontend pollt
    GET /api/components/generate/{job_id} bis status=done|error.

    Generiert eine vollstaendige Komponente: HTML+Tailwind mit {{slot}}-Markern,
    plus Slot-Definitionen, Name, ki_prompt_hint, preview_note. Wird NICHT
    automatisch in die DB geschrieben — User muss explizit speichern via
    POST /api/components.
    """
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    cat = (body.category or "").strip().upper()
    if cat not in {"NAV", "HERO", "LEIST", "TRUST", "SEO", "CTA", "HW", "FOOT", "CUSTOM"}:
        raise HTTPException(400, f"category '{cat}' ungueltig")

    job_id = str(uuid.uuid4())
    _component_gen_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_component_gen_job,
        args=(job_id, body, api_key),
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}


@component_router.get("/generate/{job_id}")
def get_component_gen_job(job_id: str, user=Depends(require_any_auth)):
    """Polling fuer Component-Designer-Job. Cleanup nach erstem done/error-Read."""
    job = _component_gen_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        snapshot = dict(job)
        _component_gen_jobs.pop(job_id, None)
        return snapshot
    return job


def _run_component_gen_job(job_id: str, req: GenerateComponentRequest, api_key: str) -> None:
    """Background-Thread: generiert einen Block und prueft ihn gegen den Vertrag.

    Der Vertrag (`services/block_contract.py`) ist an der bestehenden Bibliothek
    gemessen. Ein erzeugter Block, der ihn verletzt, wuerde im Wireframe-Editor
    das Raster sprengen oder fremde Ressourcen einschleppen — deshalb bekommt
    das Modell die Verstoesse zurueck und eine Runde, sie zu beheben. Was danach
    noch offen ist, steht im Ergebnis und blockiert die Freigabe.
    """
    try:
        client = Anthropic(api_key=api_key)
        messages = [{"role": "user", "content": _build_designer_prompt(req)}]

        response, result = _ki_runde(client, messages)
        _pruefe_pflichtfelder(result)
        _slots_vervollstaendigen(result)
        verstoesse = pruefe(result["html_template"], slug=result["slug"],
                            slots=result["slots"])

        if verstoesse:
            logger.info("component_gen job %s: %d Verstoss/Verstoesse, eine "
                        "Reparaturrunde — %s", job_id, len(verstoesse),
                        als_text(verstoesse))
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": _reparatur_auftrag(verstoesse)})

            _, repariert = _ki_runde(client, messages)
            _pruefe_pflichtfelder(repariert)
            _slots_vervollstaendigen(repariert)
            nachher = pruefe(repariert["html_template"], slug=repariert["slug"],
                             slots=repariert["slots"])
            # Nur uebernehmen, wenn die Reparatur es wirklich besser macht.
            if len(nachher) < len(verstoesse):
                result, verstoesse = repariert, nachher
            if verstoesse:
                logger.warning("component_gen job %s: nach Reparatur weiterhin "
                               "unsauber — %s", job_id, als_text(verstoesse))

        result.setdefault("ki_prompt_hint", "")
        result.setdefault("preview_note", "")
        result.setdefault("tags", [])
        if "kas-ai" not in result["tags"]:
            result["tags"].append("kas-ai")
        result["category"] = req.category.upper()
        if req.section_hint:
            result["section_hint"] = req.section_hint

        # Der Befund faehrt mit: das Frontend zeigt ihn an, und ohne ihn
        # koennte der Block still als "fertig" durchgehen.
        result["contract"] = {
            "konform":    not verstoesse,
            "verstoesse": [{"regel": v.regel, "text": v.text} for v in verstoesse],
        }

        _component_gen_jobs[job_id] = {"status": "done", "result": result}
    except _Abbruch as exc:
        _component_gen_jobs[job_id] = {"status": "error", "error": str(exc)}
    except Exception as exc:
        logger.error(f"component_gen job {job_id} crashed: {exc}", exc_info=True)
        _component_gen_jobs[job_id] = {"status": "error", "error": str(exc)}


def _build_designer_prompt(req: GenerateComponentRequest) -> str:
    cat = req.category.upper()
    style = (req.style_vibe or "elegant").lower()
    style_text = _STYLE_GUIDANCE.get(style, _STYLE_GUIDANCE["elegant"])
    cat_text = _CATEGORY_GUIDANCE.get(cat, _CATEGORY_GUIDANCE["CUSTOM"])
    context = _industry_block(req)
    elements_block = _format_elements_block(req.elements)
    layout_block = _layout_preset_block(req.layout_preset)
    user_extra = (req.user_prompt or "").strip()
    user_block = f"\nZUSAETZLICHER USER-WUNSCH:\n{user_extra}\n" if user_extra else ""

    return f"""Du bist Senior Web-Designer fuer Marketing-Sites. Generiere genau EINE Section
in HTML+Tailwind als Wireframe, die in eine bestehende Komponenten-Bibliothek aufgenommen wird.

KATEGORIE: {cat}
{cat_text}
{layout_block}
LAYOUT-DICHTE: {style}
{style_text}

{_WIREFRAME_CONSTRAINTS}
{context}
{elements_block}
{user_block}

HARTE REGELN:
1. Output ist VALIDES HTML+Tailwind. Kein React, kein JSX, keine onClick-Handler.
2. Genau EIN Wurzelelement — `<section>`, `<header>`, `<footer>`, `<nav>` oder `<a>`,
   je nach Kategorie. Kein `<html>`/`<body>`. Das Wurzelelement traegt
   `data-block="<slug>"` mit exakt dem slug aus dem JSON-Output; daran findet
   der Editor den Block wieder.
3. Mobile-first responsive: nutze sm:/md:/lg:-Praefixe wo sinnvoll.
4. Nur Standard-Tailwind-Klassen. Keine erfundenen Klassen, keine Custom-Properties
   (kein `bg-background-primary`, kein `text-text-alternative`).
5. Semantisches HTML: `<h1>/<h2>/<h3>` fuer Headlines, `<button>` fuer Aktionen,
   `<a>` fuer Links, `<ul>/<li>` fuer Listen.
6. Accessibility: aria-label fuer icon-only-Buttons, alt="" fuer Bilder, semantic landmarks.
7. Slot-Markierung: ALLE wiederverwendbaren Texte als `{{{{slot_key}}}}`-Marker
   (doppelte geschweifte Klammern, snake_case). Beispiele: `{{{{headline}}}}`,
   `{{{{cta_label}}}}`, `{{{{feature_1_title}}}}`. Headlines, Subtexte, Button-Labels,
   Link-Texte, Logo-Text, Listen-Items werden zu Slots. Nicht jeder kleine Text —
   max. 5-15 Slots pro Section.
8. Bilder: nutze `<img>` mit `src=""` oder einen schlichten Placeholder-`<div>`
   mit Tailwind-Background. KEINE externen Bild-URLs.
9. KEINE Ressource von einem fremden Server: kein `<script>`, `<iframe>`, `<link>`,
   `<object>`, `<embed>`, kein `src="https://…"`, kein `@import`. Sonst geht die
   IP jedes Besuchers an einen Dritten, bevor er etwas angeklickt hat — das ist
   ein K.-o.-Kriterium in unserem eigenen Website-Audit. Ein `<a href="https://…">`
   zum Anklicken ist dagegen erlaubt.
10. KEIN `id`-Attribut. Der Block kann zweimal auf einer Seite stehen; die id
    waere dann doppelt. Das gilt auch fuer Barrierefreiheit: Statt
    `aria-labelledby="…"` mit `id` am Titel nimm `aria-label="<Text>"` direkt
    am Bereich — es braucht keinen Anker und bleibt bei zwei Vorkommen richtig.
11. Kein `position: fixed` / `sticky` — sprengt die Vorschau im Editor.
12. Verschachtelung hoechstens 12 Ebenen tief.
13. NUR neutrale Farbtoene: `gray`, `slate`, `zinc`, `neutral`, `stone` sowie
    `white`, `black`, `transparent`. Kein bunter Ton (`bg-blue-500`,
    `text-emerald-600` …), kein eigener Farbwert (`bg-[#004F59]`) und keine
    Farbe im `style`-Attribut. Die Farbe einer Kundenseite kommt aus ihrem
    Style-Guide und ersetzt die Graustufen — was bunt im Block steht,
    ueberlebt den Markenwechsel und steht beim Kunden falsch.

OUTPUT-FORMAT — antworte AUSSCHLIESSLICH als valides JSON, KEIN Markdown-Wrapper, KEINE Erklaerung:

{{
  "slug":           "<kleinbuchstaben-mit-bindestrich, sprechend, z.B. hero-split-foerderung>",
  "name":           "<menschenlesbarer Name auf Deutsch, max 60 Zeichen>",
  "html_template":  "<das vollstaendige HTML als String, mit \\\" escaped wenn noetig>",
  "slots": [
    {{"key": "<snake_case_key>", "label": "<deutsches Label>", "default": "<sinnvoller Default>"}}
  ],
  "ki_prompt_hint": "<1-2 Saetze: wofuer ist diese Section ideal? Welche Briefing-Aspekte triggern sie?>",
  "preview_note":   "<1 Satz technische Notiz: z.B. 'Mobile-Burger statisch, ohne JS' oder 'Drei-Spalten-Grid auf Desktop'>",
  "tags":           ["<{cat.lower()}>", "kas-ai", "tailwind", "<style: {style}>"]
}}
"""


def _ki_runde(client, messages: list) -> tuple:
    """Eine Runde beim Modell. Returnt (response, geparstes_json).

    Der scharfe Lauf vom 2026-08-13 hat gezeigt, woran ein Auftrag wirklich
    scheitert: nicht am Vertrag (eine Reparaturrunde auf zehn Bloecke), sondern
    an einer sporadisch kaputten JSON-Antwort. Zwei Nachlaeufe desselben Falls
    kamen sauber zurueck, `stop_reason` war jedes Mal `end_turn` — es war ein
    Ausrutscher, kein Muster. Deshalb bekommt das Modell den Parserfehler
    zurueck und **eine** zweite Chance; hilft die nicht, ist Schluss.

    Bei `max_tokens` wird nicht nachgefragt: Die Antwort ist dann garantiert
    unvollstaendig, und derselbe Auftrag wuerde dasselbe Limit erneut reissen.
    """
    response = _modell_aufruf(client, messages)

    if getattr(response, "stop_reason", None) == "max_tokens":
        raise _Abbruch("Die Generierung wurde abgeschnitten (max_tokens). "
                       "Bitte einen einfacheren Layout-Wunsch waehlen.")

    roh = _extract_text_from_response(response)
    try:
        return response, _als_json(roh)
    except json.JSONDecodeError as exc:
        # Der Fehler wird gebraucht, nachdem der except-Block verlassen ist —
        # Python raeumt `exc` dort selbst weg.
        parserfehler = exc
        logger.warning("component_gen: JSON-Parsing fehlgeschlagen: %s; "
                       "zweiter Versuch; raw[:300]=%r", exc, roh[:300])

    zweiter_anlauf = messages + [
        {"role": "assistant", "content": response.content},
        {"role": "user", "content": _json_nachbesserung(parserfehler)},
    ]
    response = _modell_aufruf(client, zweiter_anlauf)
    roh = _extract_text_from_response(response)
    try:
        return response, _als_json(roh)
    except json.JSONDecodeError as exc:
        logger.warning("component_gen: auch der zweite Versuch war kein JSON: "
                       "%s; raw[:300]=%r", exc, roh[:300])
        raise _Abbruch(f"KI-Output kein valides JSON: {exc}")


def _build_prompt(
    briefing: Optional[Briefing],
    pages: list[dict],
    components: list[dict],
) -> str:
    """Baut den Anthropic-Prompt fuer die Wireframe-Generation."""
    briefing_summary = "Kein Briefing verfuegbar."
    if briefing:
        parts: list[str] = []
        # Briefing-Felder, die plausibel Inhalte enthalten — defensive Nutzung,
        # damit fehlende Spalten nicht crashen.
        for field in (
            "projektrahmen", "positionierung", "leistungen",
            "einzugsgebiet", "usp", "mitbewerber",
        ):
            val = getattr(briefing, field, None) or ""
            val = val.strip() if isinstance(val, str) else ""
            if val and val != "{}":
                parts.append(f"- {field}: {val[:500]}")
        if parts:
            briefing_summary = "\n".join(parts)

    pages_text = "\n".join([
        f"- page_id={p['id']} · {p['page_name']}"
        for p in pages
    ]) or "Keine Sitemap-Seiten gefunden."

    components_text = "\n".join([
        f"- {c['slug']} [{c['category']}] {c['name']}: {c['ki_prompt_hint'] or '-'}"
        for c in components
    ])

    slot_keys_per_slug = "\n".join([
        f"- {c['slug']}: {[s.get('key') for s in (c.get('slots') or [])]}"
        for c in components
    ])

    return f"""Du bist Web-Design-Experte fuer deutsche Handwerksbetriebe.

Aufgabe: Weise jeder Sitemap-Seite die optimalen Wireframe-Bloecke aus der
Bibliothek zu und befuelle die Slots mit kundenspezifischem Copy aus dem Briefing.

BRIEFING:
{briefing_summary}

SITEMAP-SEITEN:
{pages_text}

VERFUEGBARE KOMPONENTEN-BIBLIOTHEK:
{components_text}

SLOT-KEYS PRO BLOCK (Pflicht — nutze nur diese Keys, keine erfundenen):
{slot_keys_per_slug}

REGELN:
- Pro Seite 4-8 Bloecke in sinnvoller Reihenfolge.
- Erste Seite hat IMMER eine NAV-Komponente am Anfang (order=0).
- Letzte Seite hat IMMER einen FOOT-Block am Ende.
- Trust-Bloecke einbauen wenn Briefing belastbares Material liefert.
- Slot-Werte 1:1 aus Briefing extrahieren — nicht erfinden, lieber leer lassen.
- Notdienst-Bloecke nur wenn Briefing 24h-Service erwaehnt.

Antworte AUSSCHLIESSLICH als valides JSON, KEIN Markdown-Wrapper, KEINE Erklaerung:

{{
  "pages": [
    {{
      "page_id": <int>,
      "blocks": [
        {{"slug": "<bibliotheks-slug>", "order": <int ab 0>, "slots": {{"<key>": "<wert>"}}}}
      ]
    }}
  ]
}}
"""


def _industry_block(req: GenerateComponentRequest) -> str:
    """Baut den Branchen-Kontext-Block fuer den Prompt."""
    ind = (req.industry or "shk").lower()

    # Backwards-compat: alte shk_context=False ohne industry-Field
    if req.shk_context is False and req.industry is None:
        return _GENERIC_CONTEXT

    if ind == "none":
        return _GENERIC_CONTEXT

    if ind == "custom":
        custom = (req.industry_custom or "").strip()
        if not custom:
            return _GENERIC_CONTEXT
        return f"""
BRANCHEN-KONTEXT (Custom):
{custom}

DEFAULT-WERTE: Verwende branchen-spezifische Texte. Keine "Lorem ipsum",
keine "Link One/Two", keine "Button" als Default-Texte. Realistisch,
verkaufs-fokussiert, deutscher Ton.
"""

    entry = _INDUSTRIES.get(ind)
    if not entry:
        return _GENERIC_CONTEXT

    label, topics = entry
    return f"""
BRANCHEN-KONTEXT — {label}:
Typische Themen je nach Section-Kategorie:
{topics}

DEFAULT-WERTE: Verwende branchen-spezifische Texte. Keine "Lorem ipsum",
keine "Link One/Two", keine "Button" als Default-Texte. Realistisch,
verkaufs-fokussiert, deutscher Ton.
"""


@component_router.post("/generate-copy")
def generate_section_copy(
    body: GenerateCopyRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Generiert KI-Slot-Werte fuer eine Library-Section auf Basis eines
    Free-Form-Prompts. Sync, weil Antwort klein (~1-2k tokens) und der User
    sofort feedback erwartet.

    Returnt {"slots": {key: value, ...}} — exakt die Slot-Keys der Library-Section.
    Frontend ueberschreibt damit die Slot-Inputs im Side-Panel.
    """
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    row = db.query(ComponentLibrary).filter(ComponentLibrary.slug == body.slug).first()
    if not row:
        raise HTTPException(404, f"Slug '{body.slug}' nicht gefunden")

    slots = row.slots or []
    if not slots:
        raise HTTPException(400, f"Section '{body.slug}' hat keine Slots")

    user_prompt = (body.ai_prompt or "").strip()
    if not user_prompt:
        raise HTTPException(400, "ai_prompt darf nicht leer sein")

    # Asset-/Element-Hints in den Prompt einbauen — Sonnet beruecksichtigt sie
    # beim Slot-Wert-Generieren (z.B. Button-Label wenn element_type=button).
    extra_hints = []
    if body.asset_type == "image":
        extra_hints.append("- Diese Section soll ein Bild zeigen (alt-Texte / Bild-Beschreibungen entsprechend formulieren).")
    elif body.asset_type == "video":
        extra_hints.append("- Diese Section soll ein Video einbinden (Texte koennen darauf Bezug nehmen, z.B. 'Video ansehen').")
    if body.element_type == "form":
        extra_hints.append("- Diese Section enthaelt ein Formular (CTA-Texte / Labels formular-bezogen formulieren).")
    elif body.element_type == "button":
        extra_hints.append("- Diese Section betont einen Button-CTA (klare Handlungsaufforderung im Button-Slot).")
    extras_text = "\n".join(extra_hints) if extra_hints else ""

    slot_lines = "\n".join([
        f"- {s.get('key')}: {s.get('label', s.get('key'))} (Default: {s.get('default', '')})"
        for s in slots if s.get("key")
    ])

    prompt = f"""Du befuellst Slots einer Marketing-Section mit Copy.

SECTION: {row.name} ({row.category})
HINT: {row.ki_prompt_hint or '-'}

VERFUEGBARE SLOTS (genau diese Keys, nichts erfinden):
{slot_lines}

USER-WUNSCH:
{user_prompt}

{extras_text}

REGELN:
- Antworte AUSSCHLIESSLICH als valides JSON, KEIN Markdown-Wrapper, KEINE Erklaerung.
- Schluessel = Slot-Key, Wert = generierter Text (deutsch, professionell, verkaufs-fokussiert).
- Keine Lorem ipsum, keine Platzhalter-Texte.
- Headlines praegnant (max 60 Zeichen), Subtexte 1-2 Saetze, Button-Labels max 25 Zeichen.

Output:
{{
{', '.join([f'  "{s.get("key")}": "<wert>"' for s in slots if s.get("key")])}
}}
"""

    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-5", thinking={"type": "disabled"},
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _extract_text_from_response(response)
        try:
            # strict=False wie im Generator: ein roher Zeilenumbruch in einer
            # Zeichenkette ist ein Ausrutscher, kein Grund fuer einen 502.
            generated = json.loads(raw, strict=False)
        except json.JSONDecodeError as exc:
            logger.warning(f"generate-copy: JSON-Parse fehlgeschlagen: {exc}; raw[:300]={raw[:300]!r}")
            raise HTTPException(502, f"KI-Output kein valides JSON: {exc}")

        if not isinstance(generated, dict):
            raise HTTPException(502, "KI-Output ist kein Object")

        # Filter auf valide Slot-Keys — KI haette sich erfundene Keys ausdenken koennen
        valid_keys = {s.get("key") for s in slots if s.get("key")}
        result = {k: str(v) for k, v in generated.items() if k in valid_keys}
        return {"slots": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"generate-copy crashed: {exc}", exc_info=True)
        raise HTTPException(500, f"KI-Aufruf fehlgeschlagen: {exc}")


@component_router.post("/variation")
def get_block_variation(
    body: VariationRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Schlaegt eine alternative Section gleicher Kategorie vor.

    Body:
      - current_slug:  Pflicht. Aktueller Block, fuer den eine Variation gesucht ist.
      - exclude_slugs: Optional, Liste von slugs die NICHT vorgeschlagen werden
                       sollen (z.B. die anderen Bloecke der Page, damit nicht
                       doppelt vorgeschlagen wird).

    Returnt: kompletter ComponentLibrary-Eintrag mit html_template.
    Erste Iteration: Random-Pick aus gleicher Kategorie. KI-basierte Auswahl
    folgt in spaeterem Pass falls noetig.
    """
    import random as _rnd

    current = db.query(ComponentLibrary).filter(ComponentLibrary.slug == body.current_slug).first()
    if not current:
        raise HTTPException(status_code=404, detail=f"Block '{body.current_slug}' nicht gefunden")

    q = db.query(ComponentLibrary).filter(
        ComponentLibrary.category == current.category,
        ComponentLibrary.slug != body.current_slug,
    )
    if body.exclude_slugs:
        q = q.filter(~ComponentLibrary.slug.in_(body.exclude_slugs))
    candidates = q.all()

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=f"Keine Alternativen in Kategorie '{current.category}' verfuegbar",
        )

    chosen = _rnd.choice(candidates)
    return _serialize_component(chosen, include_html=True)


def _extract_text_from_response(response) -> str:
    """Extrahiert den Text-Teil aus einer Anthropic-Messages-Response."""
    raw = ""
    for block in (response.content or []):
        if getattr(block, "type", None) == "text":
            raw += getattr(block, "text", "")
    raw = raw.strip()
    # Robust gegen versehentliche Markdown-Codefences von der KI
    if raw.startswith("```"):
        # Inhalt zwischen erstem und naechstem ``` extrahieren
        try:
            raw = raw.split("```", 2)[1]
        except IndexError:
            pass
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip("`\n ")
    return raw


_CATEGORY_GUIDANCE = {
    "NAV":   "Header-Navigation am oberen Rand der Site. Logo + Nav-Links + ggf. CTA-Button. Mobile-Burger.",
    "HERO":  "Hero-Section direkt unter der Navigation. Grosse Headline, Subtext, primaerer + sekundaerer CTA. Optional Hero-Bild oder Visual-Slot.",
    "LEIST": "Leistungs-/Feature-Section. Drei bis sechs Service-Karten oder ein Grid-Layout mit Icons + Titeln + Kurztexten.",
    "TRUST": "Trust-/Social-Proof-Section. Testimonials, Kunden-Logos, Statistiken, oder Zertifikate. Vermittelt Glaubwuerdigkeit.",
    "SEO":   "Content-Section fuer SEO. Lange Textblocks mit H2/H3-Struktur, ggf. begleitendes Bild oder Inline-CTA.",
    "CTA":   "Call-to-Action-Section. Klare Handlungs-Aufforderung: Termin vereinbaren, Anrufen, Angebot anfordern. Kontrastreiche Optik.",
    "HW":    "Hardware-/Produkt-Section. Produkt-Karten, Preise, Spezifikationen. Z.B. Waermepumpe-Modelle oder Wallbox-Pakete.",
    "FOOT":  "Footer am Site-Ende. Kontakt-Daten, Sitemap-Links, Rechtliches (Impressum, Datenschutz, AGB), ggf. Social-Icons.",
    "CUSTOM": "Allgemeine Section, semantisch nicht festgelegt. Folge den User-Vorgaben.",
}


# Der Block-Designer schreibt Markup, das in die Bibliothek wandert und danach
# auf Kundenseiten steht — hier zaehlt Qualitaet mehr als der Token-Preis.
# Die uebrigen KI-Aufrufe in dieser Datei (Slot-Copy, Wireframe-Zuordnung)
# bleiben bewusst auf dem guenstigeren Modell.
_DESIGNER_MODELL = "claude-opus-5"


_GENERIC_CONTEXT = """
ALLGEMEINER KONTEXT:
Die Section wird in einer Marketing-Site verwendet. Verwende sinnvolle
Default-Texte (keine "Lorem ipsum", keine "Link One/Two"). Realistisch,
professionell, deutscher Ton.
"""


# Layout-Dichte (NICHT Farb-Stil! Komponenten sind immer Wireframe-grau).
# Beeinflusst Whitespace, Headline-Groessen, Anzahl Elemente pro Section.
_STYLE_GUIDANCE = {
    "minimal": "Sparsam — viel Whitespace, wenige Elemente, ruhige Komposition. Headlines text-2xl/3xl, Body text-base. Padding grosszuegig (py-16, lg:py-24). Single-Column oder max. 2-Spalten-Layout.",
    "elegant": "Ausgewogen — klassisches Marketing-Site-Layout. Headlines text-3xl/4xl, Body text-base. Padding mittel (py-12, lg:py-20). Bis zu 3-Spalten-Grids.",
    "bold":    "Dicht — viele Elemente pro Section, breite Layouts, grosse Headlines (text-4xl/5xl). Padding kompakt (py-8, lg:py-16). 3-4-Spalten-Grids, viele Trust/Stat/Card-Items moeglich.",
}


def _als_json(roh: str) -> dict:
    """Parst die Antwort. `strict=False` laesst rohe Steuerzeichen in
    Zeichenketten durch — ein Zeilenumbruch mitten im Markup ist der haeufigste
    Ausrutscher und kein Grund, eine Minute Rechenzeit wegzuwerfen."""
    ergebnis = json.loads(roh, strict=False)
    if not isinstance(ergebnis, dict):
        raise _Abbruch("KI-Output ist kein Object")
    return ergebnis


def _format_elements_block(elements) -> str:
    """Baut den 'Pflicht-Elemente'-Block fuer den Prompt. Leerer String wenn nichts gewaehlt."""
    if not elements or not isinstance(elements, dict):
        return ""
    lines = []
    for key, val in elements.items():
        label = _ELEMENT_LABELS.get(key, key)
        if val is True:
            lines.append(f"- {label}: ja, einbauen")
        elif isinstance(val, int) and val > 0:
            lines.append(f"- {label}: genau {val}")
        # 0 / False / None → User will keine Vorgabe → KI entscheidet selbst
    if not lines:
        return ""
    return f"""
PFLICHT-ELEMENTE — diese muessen exakt in der Section vorkommen, in den
angegebenen Anzahlen. Andere Elemente nur bei klarem Layout-Bedarf:
""" + "\n".join(lines) + "\n"


def _json_nachbesserung(exc: json.JSONDecodeError) -> str:
    return f"""Deine Antwort war kein gueltiges JSON: {exc.msg} (Zeichen {exc.pos}).

Sende denselben Block noch einmal, diesmal als striktes JSON. Achte besonders
darauf, dass Anfuehrungszeichen im HTML mit \\" escaped sind und dass kein
Zeilenumbruch unescaped in einer Zeichenkette steht.
Antworte AUSSCHLIESSLICH mit dem JSON — kein Markdown-Wrapper, keine Erklaerung."""


def _layout_preset_block(preset_id: Optional[str]) -> str:
    """Wenn ein gueltiger Layout-Preset gewaehlt ist, baue einen Layout-Hint
    fuer den Prompt. Sonst leerer String."""
    if not preset_id:
        return ""
    preset = _LAYOUT_PRESETS.get(preset_id)
    if not preset:
        return ""
    return f"""
LAYOUT-PRESET: {preset['label']}
{preset['guidance']}
"""


def _modell_aufruf(client, messages: list):
    """Ein Aufruf beim Modell. Returnt das Response-Objekt.

    Streaming, weil mit eingeschaltetem Denken die Antwort laenger dauert als
    der Non-Streaming-Timeout der SDK erlaubt — dasselbe Muster wie im
    Wireframe-Job weiter unten.
    """
    with client.messages.stream(
        model=_DESIGNER_MODELL,
        max_tokens=16000,   # Denken und Antwort teilen sich dieses Budget
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        messages=messages,
    ) as stream:
        for _ in stream.text_stream:
            pass
        return stream.get_final_message()


def _pruefe_pflichtfelder(result: dict) -> None:
    """Struktur vor Inhalt: ohne diese Felder ist der Rest nicht pruefbar."""
    import re as _re

    for feld in ("slug", "name", "html_template", "slots"):
        if feld not in result:
            raise _Abbruch(f"KI-Output fehlt Pflichtfeld '{feld}'")

    slug = str(result["slug"]).strip().lower()
    if not _re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise _Abbruch(f"slug '{result['slug']}' passt nicht zur Konvention "
                       f"(kleinbuchstaben-mit-bindestrich)")
    result["slug"] = slug

    if not isinstance(result["html_template"], str) or len(result["html_template"]) < 50:
        raise _Abbruch("html_template fehlt oder zu kurz")
    if not isinstance(result["slots"], list):
        raise _Abbruch("slots muss Array sein")


def _reparatur_auftrag(verstoesse) -> str:
    zeilen = "\n".join(f"- {v}" for v in verstoesse)
    return f"""Der Block verletzt den Vertrag der Bibliothek:

{zeilen}

Behebe genau diese Punkte. Layout, Texte und Slots bleiben sonst unveraendert.
Antworte erneut AUSSCHLIESSLICH mit dem vollstaendigen JSON im selben Format —
kein Markdown-Wrapper, keine Erklaerung."""


def _slots_vervollstaendigen(result: dict) -> None:
    """Traegt Slots nach, die nur im Markup stehen.

    Der einzige Vertragsverstoss im scharfen Lauf war genau dieser, zwoelfmal
    hintereinander. Die Angabe steht im Markup — sie wird abgelesen, nicht in
    einer zweiten Runde erfragt (das kostete dort 11k Eingabe-Token).
    """
    ergaenzt = ergaenze_fehlende_slots(result.get("html_template", ""),
                                       result.get("slots") or [])
    nachgetragen = len(ergaenzt) - len(result.get("slots") or [])
    if nachgetragen:
        logger.info("component_gen: %d Slot-Angabe(n) aus dem Markup ergaenzt",
                    nachgetragen)
    result["slots"] = ergaenzt
