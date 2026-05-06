"""
Component-Library + KI-Wireframe-Generator (Step D des Online-Fertig-Redesigns).

Endpoints:
  GET  /api/components                            → alle Bloecke (Filter ?category=)
  GET  /api/components/{slug}                     → ein Block inkl. html_template
  GET  /api/projects/{id}/wireframe               → gespeicherter Wireframe
  POST /api/projects/{id}/wireframe               → manueller Save (Block-Tausch im UI)
  POST /api/projects/{id}/wireframe/generate      → KI-Job startet, returnt job_id
  GET  /api/projects/wireframe-jobs/{job_id}      → Polling fuer KI-Job

Pattern fuer den KI-Generator: Background-Thread + In-Memory-Job-Store
(analog zu routers/agents.py:_jobs und zur generate-all-Refactor in
routers/content.py). Sync Anthropic-API ueber threading.Thread, da der
SDK-Call selbst kein await ist.

Kontext fuer den Prompt: Briefing (legacy + neue Felder) + Sitemap-Seiten
des Projekts + alle ComponentLibrary-Eintraege mit ihren ki_prompt_hint.
Output: JSON wie in database.py:Project.wireframe_data dokumentiert.
"""
import json
import logging
import os
import threading
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import (
    Briefing,
    ComponentLibrary,
    Project,
    SessionLocal,
    get_db,
)
from routers.auth_router import require_any_auth

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)

# In-Memory Job-Store fuer den KI-Generator.
# { job_id: { "status": "running"|"done"|"error", "result": dict|None, "error": str|None } }
_wireframe_jobs: dict = {}

# Separater Job-Store fuer den Component-Designer (KI-Komponenten-Generator).
# { job_id: { "status": "running"|"done"|"error", "result": dict|None, "error": str|None } }
_component_gen_jobs: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# Component-Library: read-only Endpoints
# ─────────────────────────────────────────────────────────────────────────────

component_router = APIRouter(prefix="/api/components", tags=["components"])


def _serialize_component(row: ComponentLibrary, include_html: bool = False) -> dict:
    out = {
        "slug":           row.slug,
        "name":           row.name,
        "category":       row.category,
        "tags":           row.tags or [],
        "slots":          row.slots or [],
        "ki_prompt_hint": row.ki_prompt_hint or "",
        "preview_note":   row.preview_note or "",
    }
    if include_html:
        out["html_template"] = row.html_template
    return out


@component_router.get("")
def list_components(
    category: Optional[str] = None,
    include_html: bool = True,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Alle Bibliotheks-Bloecke. Optional: ?category=HERO filtert nach Kategorie.

    `include_html=true` (Default) liefert auch das `html_template` zurueck,
    weil das Wireframe-Frontend Live-Previews pro Block rendert. Caller
    der nur Metadaten brauchen koennen mit `?include_html=false` opt-out
    (~80% kleinere Response).
    """
    q = db.query(ComponentLibrary)
    if category:
        q = q.filter(ComponentLibrary.category == category.upper())
    rows = q.order_by(ComponentLibrary.category, ComponentLibrary.slug).all()
    return [_serialize_component(r, include_html=include_html) for r in rows]


@component_router.get("/{slug}")
def get_component(
    slug: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Einzelner Block inkl. HTML-Template fuer Vorschau / Render."""
    row = db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).first()
    if not row:
        raise HTTPException(status_code=404, detail="Block nicht gefunden")
    return _serialize_component(row, include_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Wireframe-W2: Variation-Vorschlag
# ─────────────────────────────────────────────────────────────────────────────

class VariationRequest(BaseModel):
    current_slug:  str
    exclude_slugs: Optional[list[str]] = None


class SaveCustomRequest(BaseModel):
    new_slug:       str
    new_name:       str
    html_template:  str
    category:       Optional[str] = "CUSTOM"
    source_slug:    Optional[str] = None
    slots:          Optional[list] = None
    ki_prompt_hint: Optional[str] = ""
    preview_note:   Optional[str] = ""


class CreateComponentRequest(BaseModel):
    slug:           str
    name:           str
    html_template:  str
    category:       str
    tags:           Optional[list[str]] = None
    slots:          Optional[list] = None
    ki_prompt_hint: Optional[str] = ""
    preview_note:   Optional[str] = ""


class UpdateComponentRequest(BaseModel):
    name:           Optional[str] = None
    html_template:  Optional[str] = None
    category:       Optional[str] = None
    tags:           Optional[list[str]] = None
    slots:          Optional[list] = None
    ki_prompt_hint: Optional[str] = None
    preview_note:   Optional[str] = None


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


@component_router.post("/save-custom")
def save_custom_component(
    body: SaveCustomRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Speichert ein User-modifiziertes HTML als neuen Custom-Library-Eintrag.

    Aufruf erfolgt aus dem Slot-Editor wenn der User „Als Custom speichern"
    auswaehlt. Der neue Eintrag erscheint danach automatisch in der
    Wireframe-Library und ist wiederverwendbar.

    Validierung:
      - new_slug darf nicht existieren (UNIQUE-Constraint waere ohnehin Fehler)
      - new_slug auf Lower-/Hyphen-Pattern beschraenkt
      - html_template darf nicht leer sein
    """
    import re as _re

    slug = (body.new_slug or "").strip().lower()
    name = (body.new_name or "").strip()
    html = (body.html_template or "").strip()
    category = (body.category or "CUSTOM").strip().upper()

    if not slug or not _re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise HTTPException(400, "new_slug muss kleinbuchstaben, ziffern, bindestriche enthalten")
    if not name:
        raise HTTPException(400, "new_name darf nicht leer sein")
    if not html or len(html) < 20:
        raise HTTPException(400, "html_template fehlt oder zu kurz")

    existing = db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).first()
    if existing:
        raise HTTPException(409, f"Slug '{slug}' existiert bereits")

    tags = ["custom", "user-saved"]
    if body.source_slug:
        tags.append(f"source:{body.source_slug}")

    row = ComponentLibrary(
        slug=slug,
        name=name,
        category=category,
        tags=tags,
        html_template=html,
        slots=body.slots or [],
        ki_prompt_hint=body.ki_prompt_hint or f"Custom-Section, abgeleitet von {body.source_slug or 'unknown'}",
        preview_note=body.preview_note or "Vom User gespeicherte Custom-Variante",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_component(row, include_html=True)


@component_router.post("")
def create_component(
    body: CreateComponentRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Legt einen neuen Library-Eintrag an (Component-Manager UI Phase 1).

    Anders als `/save-custom` ist dieser Endpoint fuer den expliziten
    "Neu anlegen"-Flow im Komponenten-Manager — Tags / Kategorie werden
    direkt vom User gewaehlt statt automatisch auf "custom" gesetzt.
    """
    import re as _re

    slug = (body.slug or "").strip().lower()
    name = (body.name or "").strip()
    html = (body.html_template or "").strip()
    category = (body.category or "").strip().upper()

    if not slug or not _re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise HTTPException(400, "slug muss kleinbuchstaben, ziffern, bindestriche enthalten")
    if not name:
        raise HTTPException(400, "name darf nicht leer sein")
    if not html or len(html) < 20:
        raise HTTPException(400, "html_template fehlt oder zu kurz")
    if not category:
        raise HTTPException(400, "category darf nicht leer sein")

    if db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).first():
        raise HTTPException(409, f"Slug '{slug}' existiert bereits")

    row = ComponentLibrary(
        slug=slug,
        name=name,
        category=category,
        tags=body.tags or [],
        html_template=html,
        slots=body.slots or [],
        ki_prompt_hint=body.ki_prompt_hint or "",
        preview_note=body.preview_note or "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_component(row, include_html=True)


@component_router.put("/{slug}")
def update_component(
    slug: str,
    body: UpdateComponentRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Aktualisiert einen Library-Eintrag. Nur uebermittelte Felder werden geaendert."""
    row = db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).first()
    if not row:
        raise HTTPException(404, f"Slug '{slug}' nicht gefunden")

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(400, "name darf nicht leer sein")
        row.name = name
    if body.html_template is not None:
        html = body.html_template.strip()
        if not html or len(html) < 20:
            raise HTTPException(400, "html_template fehlt oder zu kurz")
        row.html_template = html
    if body.category is not None:
        cat = body.category.strip().upper()
        if not cat:
            raise HTTPException(400, "category darf nicht leer sein")
        row.category = cat
    if body.tags is not None:
        row.tags = body.tags
    if body.slots is not None:
        row.slots = body.slots
    if body.ki_prompt_hint is not None:
        row.ki_prompt_hint = body.ki_prompt_hint
    if body.preview_note is not None:
        row.preview_note = body.preview_note

    db.commit()
    db.refresh(row)
    return _serialize_component(row, include_html=True)


@component_router.delete("/{slug}")
def delete_component(
    slug: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Loescht einen Library-Eintrag. Schutz: Eintraege die in einem aktiven
    Wireframe verwendet werden, koennen nicht geloescht werden — der Caller
    muss den Block dort erst tauschen."""
    row = db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).first()
    if not row:
        raise HTTPException(404, f"Slug '{slug}' nicht gefunden")

    # Defensiv: pruefen ob ein Projekt diesen slug noch im wireframe_data nutzt.
    # JSONB-Pfad: pages[*].blocks[*].slug
    in_use = db.execute(
        text("""
            SELECT id, lead_id
            FROM projects
            WHERE wireframe_data IS NOT NULL
              AND wireframe_data::text LIKE :pattern
            LIMIT 1
        """),
        {"pattern": f'%"slug": "{slug}"%'},
    ).fetchone()
    if in_use:
        raise HTTPException(
            409,
            f"Slug '{slug}' wird in Projekt #{in_use[0]} (Lead {in_use[1]}) noch verwendet — "
            "bitte dort erst tauschen.",
        )

    db.delete(row)
    db.commit()
    return {"status": "deleted", "slug": slug}


# ─────────────────────────────────────────────────────────────────────────────
# Component-Designer: KI generiert neue Komponenten on-demand
# ─────────────────────────────────────────────────────────────────────────────

class GenerateComponentRequest(BaseModel):
    category:    str                    # NAV / HERO / LEIST / TRUST / SEO / CTA / HW / FOOT / CUSTOM
    style_vibe:  Optional[str] = "elegant"  # minimal | elegant | bold
    user_prompt: Optional[str] = ""     # Free-Form-Wunsch vom User (z.B. "Hero mit Foerder-Badge")
    shk_context: Optional[bool] = True  # SHK-Branche-Kontext im Prompt setzen
    section_hint: Optional[str] = None  # Optional: spezifischer KAS-section_catalog-Hint


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


# ── Generator-Logik (Background-Thread) ──────────────────────────────────────

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

_STYLE_GUIDANCE = {
    "minimal": "Klares Layout mit viel Whitespace. Neutrale Farben (Grautoene, Weiss). Sans-Serif. Wenig Deko, max. ein Akzent. Borders sparsam. Tailwind: text-gray-700, bg-white, border-gray-200.",
    "elegant": "Refinierte Typografie mit klarer Hierarchie. Akzentfarbe gezielt einsetzen (Tailwind: indigo-600, teal-600, oder slate-800). Leichte Schatten, runde Ecken (rounded-lg). Padding grosszuegig.",
    "bold":    "Starke Farben (Tailwind: gray-900, indigo-600, amber-500). Grosse Headlines (text-4xl/5xl). Hohe Kontraste. Solid-Buttons mit eindeutigen CTAs. Mutige Akzent-Sections.",
}

_SHK_CONTEXT = """
SHK-BRANCHEN-KONTEXT (Heizung/Sanitaer/Elektrik):
Themen die in der Section vorkommen koennen, abhaengig von Kategorie:
- Waermepumpe-Beratung, Installation, Foerderung (BAFA, KfW)
- Wallbox-Installation mit THG-Quote, Foerderungs-Hinweisen
- Heizungstausch / Modernisierung mit gesetzlichen Aspekten (GEG)
- Notdienst 24/7 / Wartungsvertrag
- Beratungstermin / Kostenvoranschlag / Vor-Ort-Besichtigung
- Lokale Verankerung (Region, Meisterbetrieb, Innungsmitglied)

DEFAULT-WERTE: Verwende SHK-spezifische Texte. Keine "Lorem ipsum", keine
"Link One/Two", keine "Button" als Default-Texte. Realistisch,
verkaufs-fokussiert, deutscher Ton.
"""

_GENERIC_CONTEXT = """
ALLGEMEINER KONTEXT:
Die Section wird in einer Marketing-Site verwendet. Verwende sinnvolle
Default-Texte (keine "Lorem ipsum"). Wenn ohne spezifische Branche, halte
Texte allgemein professionell.
"""


def _build_designer_prompt(req: GenerateComponentRequest) -> str:
    cat = req.category.upper()
    style = (req.style_vibe or "elegant").lower()
    style_text = _STYLE_GUIDANCE.get(style, _STYLE_GUIDANCE["elegant"])
    cat_text = _CATEGORY_GUIDANCE.get(cat, _CATEGORY_GUIDANCE["CUSTOM"])
    context = _SHK_CONTEXT if req.shk_context else _GENERIC_CONTEXT
    user_extra = (req.user_prompt or "").strip()
    user_block = f"\nZUSAETZLICHER USER-WUNSCH:\n{user_extra}\n" if user_extra else ""

    return f"""Du bist Senior Web-Designer fuer Marketing-Sites. Generiere genau EINE Section
in HTML+Tailwind, die in eine bestehende Komponenten-Bibliothek aufgenommen wird.

KATEGORIE: {cat}
{cat_text}

STYLE-VIBE: {style}
{style_text}

{context}
{user_block}

HARTE REGELN:
1. Output ist VALIDES HTML+Tailwind. Kein React, kein JSX, keine onClick-Handler.
2. Eine einzige aeussere `<section>` (oder `<header>`/`<footer>`) als Wurzel — kein `<html>`/`<body>`.
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

OUTPUT-FORMAT — antworte AUSSCHLIESSLICH als valides JSON, KEIN Markdown-Wrapper, KEINE Erklaerung:

{{
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


def _run_component_gen_job(job_id: str, req: GenerateComponentRequest, api_key: str) -> None:
    """Background-Thread: ruft Sonnet, parst JSON, speichert Resultat in Job-Store."""
    try:
        prompt = _build_designer_prompt(req)
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,  # ein Section-HTML ist ~2-5k tokens, mit Slots-JSON ~6-7k
            messages=[{"role": "user", "content": prompt}],
        )
        stop_reason = getattr(response, "stop_reason", None)
        raw = _extract_text_from_response(response)

        if stop_reason == "max_tokens":
            _component_gen_jobs[job_id] = {
                "status": "error",
                "error": "Generierung wurde abgeschnitten (max_tokens). Bitte einfacheren Style/Prompt waehlen.",
            }
            return

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning(
                f"component_gen job {job_id}: JSON-Parsing fehlgeschlagen: {exc}; "
                f"raw[:300]={raw[:300]!r}"
            )
            _component_gen_jobs[job_id] = {
                "status": "error",
                "error": f"KI-Output kein valides JSON: {exc}",
            }
            return

        # Validation
        for field in ("name", "html_template", "slots"):
            if field not in result:
                _component_gen_jobs[job_id] = {
                    "status": "error",
                    "error": f"KI-Output fehlt Pflichtfeld '{field}'",
                }
                return
        if not isinstance(result["html_template"], str) or len(result["html_template"]) < 50:
            _component_gen_jobs[job_id] = {
                "status": "error",
                "error": "html_template fehlt oder zu kurz",
            }
            return
        if not isinstance(result["slots"], list):
            _component_gen_jobs[job_id] = {
                "status": "error",
                "error": "slots muss Array sein",
            }
            return

        # Defaults setzen + Kategorie/section_hint anreichern
        result.setdefault("ki_prompt_hint", "")
        result.setdefault("preview_note", "")
        result.setdefault("tags", [])
        if "kas-ai" not in result["tags"]:
            result["tags"].append("kas-ai")
        result["category"] = req.category.upper()
        if req.section_hint:
            result["section_hint"] = req.section_hint

        _component_gen_jobs[job_id] = {"status": "done", "result": result}
    except Exception as exc:
        logger.error(f"component_gen job {job_id} crashed: {exc}", exc_info=True)
        _component_gen_jobs[job_id] = {"status": "error", "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Wireframe pro Projekt: Read / manueller Save / KI-Generator
# ─────────────────────────────────────────────────────────────────────────────

wireframe_router = APIRouter(prefix="/api/projects", tags=["wireframe"])


class WireframeBlock(BaseModel):
    slug: str
    order: int = 0
    slots: dict = {}


class WireframePage(BaseModel):
    page_id: int
    page_name: Optional[str] = None
    blocks: list[WireframeBlock] = []


class WireframeData(BaseModel):
    """
    Persistent store fuer den Online-Fertig-Editor.
    pages              — vom KI-Wireframe-Generator oder manuellem Block-Tausch
    style_guide        — Tokens aus StyleGuideView (Farben/Typo/Buttons/Spacing)
    style_guide_approved — Gate fuer DesignView (Step E)
    """
    pages: list[WireframePage] = []
    style_guide: Optional[dict] = None
    style_guide_approved: Optional[bool] = False


@wireframe_router.get("/{project_id}/wireframe")
def get_wireframe(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Gespeicherten Wireframe abrufen. Leere Struktur wenn noch nichts."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return proj.wireframe_data or {"pages": []}


@wireframe_router.post("/{project_id}/wireframe")
def save_wireframe(
    project_id: int,
    data: WireframeData,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Manueller Save (Block-Tausch im UI, ohne KI)."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    proj.wireframe_data = data.dict()
    db.commit()
    return {"status": "saved", "page_count": len(data.pages)}


# Polling-Endpoint fuer KI-Jobs unter /wireframe-jobs/ — eindeutiger Pfad,
# damit FastAPI nicht mit /{project_id}/wireframe kollidiert.
@wireframe_router.get("/wireframe-jobs/{job_id}")
def get_wireframe_job(job_id: str, user=Depends(require_any_auth)):
    """Polling fuer KI-Job. Cleanup nach erstem Read von done/error."""
    job = _wireframe_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        snapshot = dict(job)
        _wireframe_jobs.pop(job_id, None)
        return snapshot
    return job


@wireframe_router.post("/{project_id}/wireframe/generate")
def generate_wireframe(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Startet KI-Wireframe-Generierung als Background-Job.

    Returnt sofort `{job_id, status: 'running'}` — Frontend pollt
    `GET /api/projects/wireframe-jobs/{job_id}` bis status=done|error.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    if not Anthropic:
        raise HTTPException(status_code=500, detail="anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY nicht konfiguriert")

    job_id = str(uuid.uuid4())
    _wireframe_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_wireframe_job,
        args=(job_id, project_id, api_key),
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}


# ─────────────────────────────────────────────────────────────────────────────
# KI-Generator-Logik (Background-Thread)
# ─────────────────────────────────────────────────────────────────────────────

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


def _run_wireframe_job(job_id: str, project_id: int, api_key: str) -> None:
    """Background-Thread — laedt DB-Daten, ruft Claude, speichert Resultat."""
    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            _wireframe_jobs[job_id] = {"status": "error", "error": "Projekt verschwunden"}
            return

        briefing = db.query(Briefing).filter(Briefing.lead_id == proj.lead_id).first()

        pages_rows = db.execute(text("""
            SELECT id, page_name
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY parent_id NULLS FIRST, position, id
        """), {"lid": proj.lead_id}).fetchall()
        pages = [{"id": r[0], "page_name": r[1]} for r in pages_rows]
        if not pages:
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": "Keine Sitemap-Seiten — bitte zuerst Sitemap generieren.",
            }
            return

        components_rows = db.query(ComponentLibrary).all()
        if not components_rows:
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": "Komponenten-Bibliothek leer — Seed nicht gelaufen?",
            }
            return
        components = [{
            "slug":           r.slug,
            "category":       r.category,
            "name":           r.name,
            "ki_prompt_hint": r.ki_prompt_hint or "",
            "slots":          r.slots or [],
        } for r in components_rows]

        prompt = _build_prompt(briefing, pages, components)

        client = Anthropic(api_key=api_key)
        # max_tokens=32000 deckt grosse Sitemaps ab (~50 Seiten x 8 Bloecke).
        # Vorher 4000 → JSON wurde bei groesseren Wireframes mitten im String
        # abgeschnitten, json.loads kippte mit "Unterminated string". Anthropic
        # rechnet nur tatsaechlich generierte Tokens ab, daher kein Cost-Risiko.
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=32000,
            messages=[{"role": "user", "content": prompt}],
        )
        stop_reason = getattr(response, "stop_reason", None)
        raw_text = _extract_text_from_response(response)

        # Wenn das Modell wegen max_tokens gestoppt hat, ist der JSON-Output
        # garantiert truncated — klarer Fehler statt obskurem JSON-Parse-Error.
        if stop_reason == "max_tokens":
            logger.warning(
                f"wireframe job {job_id}: stop_reason=max_tokens, output truncated "
                f"({len(raw_text)} chars); pages={len(pages)}, components={len(components)}"
            )
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": (
                    "KI-Output wurde abgeschnitten (max_tokens erreicht). "
                    "Sitemap mit weniger Seiten erneut generieren oder Limit erhoehen."
                ),
            }
            return

        try:
            wireframe = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                f"wireframe job {job_id}: JSON-Parsing fehlgeschlagen: {exc}; "
                f"stop_reason={stop_reason}; raw_len={len(raw_text)}; "
                f"raw[:300]={raw_text[:300]!r}"
            )
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": f"KI-Output kein valides JSON: {exc}",
            }
            return

        if not isinstance(wireframe, dict) or "pages" not in wireframe:
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": "KI-Output fehlt 'pages'",
            }
            return

        # Persistieren — frische Query, weil der Thread eine andere Session hat.
        # Style-Guide + Freigabe-Flag werden NICHT ueberschrieben — KI-Generator
        # bestimmt nur die pages-Struktur, alles andere bleibt erhalten.
        proj_for_write = db.query(Project).filter(Project.id == project_id).first()
        if proj_for_write is not None:
            existing = proj_for_write.wireframe_data or {}
            if not isinstance(existing, dict):
                existing = {}
            merged = {**existing, "pages": wireframe.get("pages") or []}
            proj_for_write.wireframe_data = merged
            db.commit()

        _wireframe_jobs[job_id] = {
            "status":     "done",
            "page_count": len(wireframe.get("pages") or []),
            "result":     wireframe,
        }
    except Exception as exc:
        logger.error(f"wireframe job {job_id} crashed: {exc}", exc_info=True)
        _wireframe_jobs[job_id] = {"status": "error", "error": str(exc)}
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()
