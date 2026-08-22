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
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from database import (
    Briefing,
    ComponentLibrary,
    Project,
    SessionLocal,
    get_db,
)
from routers.auth_router import require_any_auth, require_innendienst
from services.block_contract import als_text, pruefe, slots_im_markup
from services.block_slots import ergaenze_fehlende_slots
from services.block_variant import VariantenAbbruch, erzeuge_variante
from services.page_composer import KompositionsAbbruch, komponiere

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)

# Der Block-Designer schreibt Markup, das in die Bibliothek wandert und danach
# auf Kundenseiten steht — hier zaehlt Qualitaet mehr als der Token-Preis.
# Die uebrigen KI-Aufrufe in dieser Datei (Slot-Copy, Wireframe-Zuordnung)
# bleiben bewusst auf dem guenstigeren Modell.
_DESIGNER_MODELL = "claude-opus-5"

# In-Memory Job-Store fuer den KI-Generator.
# { job_id: { "status": "running"|"done"|"error", "result": dict|None, "error": str|None } }
_wireframe_jobs: dict = {}

# Separater Job-Store fuer den Component-Designer (KI-Komponenten-Generator).
# { job_id: { "status": "running"|"done"|"error", "result": dict|None, "error": str|None } }
_component_gen_jobs: dict = {}

# Stufe B: ein Block, fuer einen Kunden umgeschrieben.
_variant_jobs: dict = {}

# Stufe C: die Abfolge einer ganzen Seite.
_compose_jobs: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# Component-Library: read-only Endpoints
# ─────────────────────────────────────────────────────────────────────────────

# Die Bausteine der Kundenseiten — anlegen, freigeben, loeschen. Innendienst
# (L-67, 22.08.2026). Vor dem Setzen gemessen, wer `/api/components` aufruft:
# `App.jsx`, `menue.js`, `SettingsLayout.jsx`, `AppLayout.jsx` — kein Pfad
# unter `pages/customer/`. Die Kundenseiten selbst holen hier nichts: Sie
# liegen als fertiges HTML bei Netlify.
#
# `wireframe_router` weiter unten trug die Sperre bereits. Dass zwei Router in
# **einer** Datei verschieden gesichert waren, ist genau die Sorte
# Ungleichheit, die niemand sieht.
component_router = APIRouter(prefix="/api/components", tags=["components"],
                             dependencies=[Depends(require_innendienst)])


def _serialize_component(row: ComponentLibrary, include_html: bool = False,
                         include_contract: bool = False) -> dict:
    out = {
        "slug":           row.slug,
        "name":           row.name,
        "category":       row.category,
        "status":         row.status or "approved",
        "tags":           row.tags or [],
        "slots":          row.slots or [],
        "ki_prompt_hint": row.ki_prompt_hint or "",
        "preview_note":   row.preview_note or "",
    }
    if include_html:
        out["html_template"] = row.html_template
    if include_contract:
        out["contract"] = _befund(row.html_template or "", row.slug, row.slots or [])
    return out


def _nur_freigegebene(query):
    """Filtert Entwuerfe heraus — und behandelt NULL als freigegeben.

    `status != 'draft'` allein waere falsch: In SQL ist `NULL != 'draft'`
    nicht wahr, sondern NULL, also faellt jede Zeile ohne Status heraus. Genau
    das passiert bei Bloecken, die vor der Spalte angelegt wurden oder die der
    Bibliotheks-Seed per rohem SQL schreibt — die ganze Bibliothek waere
    unsichtbar, ohne dass irgendwo ein Fehler erschiene.
    """
    return query.filter(func.coalesce(ComponentLibrary.status, "approved") != "draft")


def _befund(html: str, slug: str, slots) -> dict:
    """Der Vertragsbefund eines Blocks, so wie ihn die API zurueckgibt."""
    verstoesse = pruefe(html, slug=slug, slots=slots)
    return {
        "konform":    not verstoesse,
        "verstoesse": [{"regel": v.regel, "text": v.text} for v in verstoesse],
    }


@component_router.get("")
def list_components(
    category: Optional[str] = None,
    include_html: bool = True,
    include_drafts: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Alle Bibliotheks-Bloecke. Optional: ?category=HERO filtert nach Kategorie.

    `include_html=true` (Default) liefert auch das `html_template` zurueck,
    weil das Wireframe-Frontend Live-Previews pro Block rendert. Caller
    der nur Metadaten brauchen koennen mit `?include_html=false` opt-out
    (~80% kleinere Response).

    Mit `include_drafts=true` faehrt zu jedem Block auch sein `contract`-Befund
    mit. Ohne ihn zeigt die Bibliotheks-Oberflaeche zwar den Entwurfs-Status,
    aber nicht den Grund — und ein Entwurf ohne Grund sieht aus wie ein Fehler.
    Der Wireframe-Editor (Default, ohne Entwuerfe) zahlt die Pruefung nicht mit.
    """
    q = db.query(ComponentLibrary)
    # Entwuerfe nur auf ausdruecklichen Wunsch — sonst taucht ungepruefter
    # Block im Wireframe-Editor auf, als waere er Bestand.
    q = q if include_drafts else _nur_freigegebene(q)
    if category:
        q = q.filter(ComponentLibrary.category == category.upper())
    rows = q.order_by(ComponentLibrary.category, ComponentLibrary.slug).all()
    return [
        _serialize_component(r, include_html=include_html,
                             include_contract=include_drafts)
        for r in rows
    ]


# ACHTUNG Reihenfolge: Diese Route MUSS vor "/{slug}" stehen. FastAPI matcht in
# Registrierungsreihenfolge — steht "/{slug}" davor, faengt es "/layout-presets"
# ab und liefert 404 "Block nicht gefunden". Gleiches gilt fuer jede weitere
# GET-Route mit einem festen Segment unterhalb von /api/components.
@component_router.get("/layout-presets")
def list_layout_presets(user=Depends(require_any_auth)):
    """Listet alle verfuegbaren Layout-Presets — Frontend rendert daraus
    den 'Layout'-Selector im KI-Component-Designer.

    Returnt Array von { id, category, label, guidance }.
    """
    return [
        {"id": pid, **meta}
        for pid, meta in _LAYOUT_PRESETS.items()
    ]


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


class GenerateCopyRequest(BaseModel):
    """Sync KI-Call: generiert Slot-Werte fuer eine bestehende Library-Section.

    Wird vom Section-Detail-Panel im WireframeView aufgerufen, wenn der User
    auf 'Generate copy' klickt. Anders als /generate (Background-Job, neue
    Section) ist das hier synchron und schnell — nur Slot-Werte, kein HTML.
    """
    slug:           str
    ai_prompt:      str                                 # Free-Form-Wunsch fuer diese Section
    asset_type:     Optional[str] = None                # 'image' | 'video' | None
    element_type:   Optional[str] = None                # 'form' | 'button' | None
    current_slots:  Optional[dict] = None               # bestehende Werte als Kontext


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

    # Gleiche Regel wie beim Neuanlegen: unsauber heisst Entwurf, nicht verworfen.
    befund = _befund(html, slug, body.slots or [])

    row = ComponentLibrary(
        slug=slug,
        name=name,
        category=category,
        status="approved" if befund["konform"] else "draft",
        tags=tags,
        html_template=html,
        slots=body.slots or [],
        ki_prompt_hint=body.ki_prompt_hint or f"Custom-Section, abgeleitet von {body.source_slug or 'unknown'}",
        preview_note=body.preview_note or "Vom User gespeicherte Custom-Variante",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {**_serialize_component(row, include_html=True), "contract": befund}


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

    # Ein Block mit offenen Verstoessen wird gespeichert, aber nicht freigegeben.
    # Verwerfen waere schlimmer: die Arbeit ginge verloren und der Nutzer saehe
    # nie, woran es lag. Als Entwurf taucht er nicht im Wireframe-Editor auf.
    befund = _befund(html, slug, body.slots or [])

    row = ComponentLibrary(
        slug=slug,
        name=name,
        category=category,
        status="approved" if befund["konform"] else "draft",
        tags=body.tags or [],
        html_template=html,
        slots=body.slots or [],
        ki_prompt_hint=body.ki_prompt_hint or "",
        preview_note=body.preview_note or "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {**_serialize_component(row, include_html=True), "contract": befund}


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

    # Nach jeder Aenderung neu pruefen. Sonst bliebe ein einmal freigegebener
    # Block freigegeben, auch wenn ihn eine spaetere Bearbeitung kaputt macht.
    befund = _befund(row.html_template, row.slug, row.slots or [])
    if not befund["konform"] and row.status != "draft":
        logger.info("Block %s faellt durch Bearbeitung auf Entwurf zurueck: %s",
                    row.slug, "; ".join(v["text"] for v in befund["verstoesse"]))
        row.status = "draft"

    db.commit()
    db.refresh(row)
    return {**_serialize_component(row, include_html=True), "contract": befund}


@component_router.post("/{slug}/approve")
def approve_component(
    slug: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Gibt einen Entwurf fuer den Wireframe-Editor frei.

    Die Freigabe ist der Punkt, an dem ein Block auf Kundenseiten landen kann.
    Solange der Vertrag verletzt ist, wird sie verweigert — mit den konkreten
    Verstoessen im Fehler, damit klar ist, was zu tun ist.
    """
    row = db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).first()
    if not row:
        raise HTTPException(404, f"Slug '{slug}' nicht gefunden")

    befund = _befund(row.html_template, row.slug, row.slots or [])
    if not befund["konform"]:
        raise HTTPException(422, {
            "message": f"Block '{slug}' verletzt den Vertrag und kann nicht "
                       f"freigegeben werden.",
            "contract": befund,
        })

    row.status = "approved"
    db.commit()
    db.refresh(row)
    return {**_serialize_component(row, include_html=True), "contract": befund}


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
    category:        str                       # NAV / HERO / LEIST / TRUST / SEO / CTA / HW / FOOT / CUSTOM
    style_vibe:      Optional[str] = "elegant"  # minimal | elegant | bold
    user_prompt:     Optional[str] = ""         # Free-Form-Wunsch vom User
    industry:        Optional[str] = "shk"      # Branchen-Key (siehe _INDUSTRIES). 'custom' nutzt industry_custom, 'none' = generisch
    industry_custom: Optional[str] = None       # Free-Form-Branchen-Beschreibung wenn industry='custom'
    elements:        Optional[dict] = None      # Pflicht-Elemente: {headline:2, buttons:2, images:4, logo:true, dropdown:false, ...}
    section_hint:    Optional[str] = None       # Optional: spezifischer KAS-section_catalog-Hint
    # Phase A (Weg 1): Layout-Preset (siehe _LAYOUT_PRESETS) — gibt der KI eine
    # konkrete Layout-Vorgabe statt freie Komposition. None = KI entscheidet.
    layout_preset:   Optional[str] = None
    # Backwards-compat: shk_context wird ignoriert wenn industry gesetzt ist
    shk_context:     Optional[bool] = None


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

# Layout-Dichte (NICHT Farb-Stil! Komponenten sind immer Wireframe-grau).
# Beeinflusst Whitespace, Headline-Groessen, Anzahl Elemente pro Section.
_STYLE_GUIDANCE = {
    "minimal": "Sparsam — viel Whitespace, wenige Elemente, ruhige Komposition. Headlines text-2xl/3xl, Body text-base. Padding grosszuegig (py-16, lg:py-24). Single-Column oder max. 2-Spalten-Layout.",
    "elegant": "Ausgewogen — klassisches Marketing-Site-Layout. Headlines text-3xl/4xl, Body text-base. Padding mittel (py-12, lg:py-20). Bis zu 3-Spalten-Grids.",
    "bold":    "Dicht — viele Elemente pro Section, breite Layouts, grosse Headlines (text-4xl/5xl). Padding kompakt (py-8, lg:py-16). 3-4-Spalten-Grids, viele Trust/Stat/Card-Items moeglich.",
}

# Wireframe-Stil-Constraints — gilt fuer ALLE Generierungen, unabhaengig vom
# Style-Vibe. Komponenten kommen in eine Wireframe-Bibliothek; das eigentliche
# CI-Design (Brand-Farben, Schriften, Akzente) wird spaeter im Projekt-Prozess
# pro Kunde appliziert. Hier zaehlt nur Struktur + Hierarchie.
_WIREFRAME_CONSTRAINTS = """
WIREFRAME-STIL (PFLICHT — KEINE Brand-Farben, KEINE bunten Akzente):

Farb-Palette — NUR diese Tailwind-Klassen:
- Hintergruende: bg-white, bg-gray-50, bg-gray-100
- Borders: border-gray-200, border-gray-300
- Text: text-gray-900 (Headlines), text-gray-700 (Body), text-gray-500 (Subtext/Mutiert)
- Primary-Button: bg-gray-900 text-white
- Secondary-Button: bg-white border border-gray-300 text-gray-900
- Inverted-Section (sparsam): bg-gray-900 text-white

VERBOTEN: bg-blue-*, bg-indigo-*, bg-amber-*, bg-emerald-*, bg-rose-*, bg-purple-*,
text-blue-*, text-indigo-* etc. Keine bunten Tailwind-Farben.
VERBOTEN: Gradients (bg-gradient-*), starke Schatten (shadow-xl, shadow-2xl).
VERBOTEN: Custom-Hex (#FF...).
ERLAUBT: shadow-sm, shadow (subtle, einsetzen wenn Layout-relevant).

Bilder/Logos/Avatare als neutrale Placeholder:
- Statt <img src="..."> immer ein Tailwind-Placeholder-Block:
  <div class="bg-gray-200 aspect-video flex items-center justify-center text-gray-500">
    <svg ...>Bild-Icon</svg>
  </div>
  Aspect-Ratios: aspect-video (16:9), aspect-square (1:1), aspect-[4/3] etc.
- Logos werden zu Text-Slots ({{logo_text}}) — KEIN Image.
- Avatare als runde Placeholder: <div class="size-12 rounded-full bg-gray-300">

Icons:
- Inline-SVG mit fill="none" stroke="currentColor". Klassen: text-gray-700, size-5 oder size-6.
- Keine Emojis, keine externen Icon-Libraries (kein lucide-react, kein heroicons-cdn).
- Generic genug halten: heart, check, arrow-right, plus, search, menu, x, mail, phone.

Hintergrund-Hinweis fuer Sonnet: Diese Section kommt in eine Wireframe-Bibliothek.
Das eigentliche Brand-Design (CI-Farben, Schriften, dekorative Akzente) wird
spaeter im Projekt-Prozess pro Kunde appliziert. Wireframe = Struktur + Hierarchie +
Semantik. Es ist NICHT das finale Design.
"""

# Branchen-Kontexte. Tuple (label, topic-list). Topic-Liste wird in den Prompt
# eingebaut, damit Sonnet branchen-spezifische Default-Werte schreibt.
_INDUSTRIES = {
    "shk": (
        "SHK (Heizung/Sanitaer/Elektrik)",
        "Waermepumpe-Beratung/-Installation/-Foerderung (BAFA, KfW), Wallbox-Installation mit THG-Quote, "
        "Heizungstausch/Modernisierung (GEG), Notdienst 24/7, Wartungsvertrag, Beratungstermin/Kostenvoranschlag, "
        "Innung/Meisterbetrieb, lokale Verankerung."
    ),
    "bauhandwerk": (
        "Bauhandwerk (Maurer, Dachdecker, Trockenbau, Zimmerei)",
        "Sanierung, Neubau, Dachdaemmung/Energetische Sanierung, Gewerk-Koordination, Festpreis-Angebot, "
        "Termintreue, Innung, Bauleitung, Referenzobjekte."
    ),
    "gala": (
        "Garten- und Landschaftsbau",
        "Aussenanlagen-Gestaltung, Pflasterung/Wegebau, Gartendesign, Bewaesserung, Hecken-/Baumschnitt, "
        "Teich/Pool, Saisonpflege, Gartenplanung mit 3D-Visualisierung."
    ),
    "maler": (
        "Maler & Stuckateur",
        "Innen-/Aussenanstrich, Fassadenrenovierung, Stuckarbeiten, Daemmsysteme (WDVS), Schimmelsanierung, "
        "Tapezierarbeiten, Sonderwuensche/Dekorputz, Farbberatung."
    ),
    "kfz": (
        "KFZ-Werkstatt / Auto-Service",
        "Inspektion, TUEV/AU, Reifenwechsel, Klimaservice, E-Auto-Service inkl. Hochvolt-Zertifizierung, "
        "Unfallinstandsetzung, Hol-/Bring-Service, Hersteller-Zertifizierungen."
    ),
    "steuer-anwalt": (
        "Steuerberater / Rechtsanwalt / Versicherungsmakler",
        "Erstberatung, Mandant-Onboarding, digitale Aktenuebergabe, Spezialisierungen (z.B. Erbrecht, "
        "Existenzgruendung, IT-Recht), Honorar-Transparenz, Vertraulichkeit, persoenliche Erreichbarkeit."
    ),
    "medizin": (
        "Arzt / Zahnarzt / Praxis / Therapie",
        "Termin-Buchung online, Sprechzeiten, Notdienst-Hinweis, Spezialisierungen, Vorsorge/Praeventiv, "
        "barrierefreier Zugang, Privat/Kassen, Patienten-Komfort."
    ),
    "gastro": (
        "Gastronomie / Hotel / Restaurant",
        "Reservierung, Speisekarte, Events/Catering, Oeffnungszeiten, regionale Kueche/Bio-Zutaten, "
        "Wein-/Getraenkekarte, Atmosphaere, Gutscheine, Gaeste-Bewertungen."
    ),
    "kosmetik": (
        "Friseur / Kosmetik / Wellness / Spa",
        "Online-Termin, Behandlungs-Menue, Produkt-Linien, Preisstaffel (Damen/Herren), "
        "Specials/Saison-Aktionen, Geschenkgutscheine, Ambiente/Studio-Tour."
    ),
    "fitness": (
        "Fitness-Studio / Sport / Yoga / Personal Training",
        "Probetraining, Mitgliedschaft (Tarife), Kursplan, Trainer-Profile, Geraete/Equipment, "
        "Ernaehrungs-/Reha-Coaching, Online-Kurse, Family-/Studenten-Tarife."
    ),
}

_GENERIC_CONTEXT = """
ALLGEMEINER KONTEXT:
Die Section wird in einer Marketing-Site verwendet. Verwende sinnvolle
Default-Texte (keine "Lorem ipsum", keine "Link One/Two"). Realistisch,
professionell, deutscher Ton.
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


_ELEMENT_LABELS = {
    "headline":    "Headlines (H1/H2/H3)",
    "subtext":     "Subtexte / Paragraphen",
    "buttons":     "Buttons / CTAs",
    "links":       "Links / Nav-Links",
    "images":      "Bilder",
    "icons":       "Icons (SVG inline)",
    "cards":       "Karten / Feature-Items / Service-Items",
    "avatars":     "Avatare / Personen-Bilder",
    "stats":       "Statistik-Counter / Zahlen-Badges",
    "form_fields": "Formular-Felder",
    "logo":        "Logo (als Text-Slot oder Image-Placeholder)",
    "dropdown":    "Dropdown / Select-Menue",
    "search":      "Such-Feld",
    "rating":      "Star-Rating-Anzeige",
    # Kein iframe: eine YouTube-Einbettung laedt beim Seitenaufruf und schickt
    # die Besucher-IP an Google, bevor jemand auf Play geklickt hat.
    "video":       "Video-Platzhalter mit Play-Icon (KEIN iframe, keine Einbettung)",
    "list":        "Liste (bullet oder numbered)",
}


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


# ── Phase A (Weg 1): Layout-Presets fuer den Component-Designer ───────────────
#
# Jeder Preset = vordefiniertes Section-Layout-Muster, das als zusaetzliche
# Hinweise an Sonnet rausgeht. So kann der User gezielt z.B. "Hero centered"
# vs "Hero off-grid" vs "Hero with-form" anfordern statt freie Komposition.
#
# Struktur: { preset_id: {"category", "label", "guidance"} }
# - category: einer der 9 KAS-Kategorien (NAV/HERO/LEIST/TRUST/SEO/CTA/HW/FOOT/CUSTOM)
# - label:    deutsches Anzeige-Label fuer das Frontend
# - guidance: 1-2 Saetze die explizit das Layout beschreiben
#
# Hinweis zur Erstellung: Diese Presets sind aus eigener Kenntnis allgemeiner
# Web-Design-Patterns entstanden. Sie sind keine Replika eines konkreten
# Drittanbieter-Templates — der Pattern-Name (z.B. "split-image",
# "off-grid", "grid-cards") ist eine generische Layout-Bezeichnung in der
# Web-Design-Community.

_LAYOUT_PRESETS = {
    # ── HERO / Header ───────────────────────────────────────────────────────
    "hero_centered": {
        "category": "HERO",
        "label":    "Hero · Zentriert",
        "guidance": "Zentrierter Hero — eine Spalte, max-w-3xl. Kicker (Eyebrow) ueber der Headline, Headline gross (text-4xl/5xl), Subtext mittig 1-2 Saetze, primaerer + sekundaerer CTA-Button nebeneinander. Kein Hero-Bild, viel Whitespace.",
    },
    "hero_split_image": {
        "category": "HERO",
        "label":    "Hero · Split (Bild rechts)",
        "guidance": "Zwei-Spalten-Layout 50/50 auf Desktop, gestapelt auf Mobile. Links: Headline + Subtext + 2 CTAs + 3 Bullet-Points. Rechts: Bild-Placeholder (aspect-video oder aspect-[4/3]).",
    },
    "hero_split_reverse": {
        "category": "HERO",
        "label":    "Hero · Split (Bild links)",
        "guidance": "Spiegelung von hero_split_image: Bild-Placeholder links, Text-Block rechts.",
    },
    "hero_with_form": {
        "category": "HERO",
        "label":    "Hero · mit Lead-Form",
        "guidance": "Zwei-Spalten-Layout. Links: Headline + Subtext + Trust-Bullets. Rechts: Karte mit Mini-Lead-Formular (Name, E-Mail, Telefon, Submit-Button). Form als Card mit border + shadow-sm.",
    },
    "hero_off_grid": {
        "category": "HERO",
        "label":    "Hero · Off-Grid",
        "guidance": "Asymmetrisches Layout: Text-Block links oben, ueberlappende Bild-Placeholder rechts mit leichtem Versatz (translate). Wirkt redaktionell. Nutze grid + col-span fuer den Versatz.",
    },
    "hero_grid_cards": {
        "category": "HERO",
        "label":    "Hero · mit Karten-Grid",
        "guidance": "Hero-Headline oben zentriert, darunter ein 3-Spalten-Grid mit Service-/Feature-Cards. Jede Card: Icon (SVG) + Titel + 1-Satz-Text. Karten sind die primaeren CTAs.",
    },
    "hero_minimal": {
        "category": "HERO",
        "label":    "Hero · Minimal",
        "guidance": "Kompakt fuer Sub-Pages: Breadcrumb + Headline + 1-Satz-Subtext. Padding sparsamer (py-12 statt py-24). Kein Bild, kein CTA.",
    },
    "hero_video": {
        "category": "HERO",
        "label":    "Hero · mit Video",
        "guidance": "Hero mit Video-Placeholder rechts (aspect-video, Play-Icon zentriert in einem dunklen Overlay-Div). Links: Text-Block wie bei split-image.",
    },

    # ── NAV / Navbar ─────────────────────────────────────────────────────────
    "nav_standard": {
        "category": "NAV",
        "label":    "Nav · Logo-Links",
        "guidance": "Klassisch: Logo links, Nav-Links zentriert, primaerer CTA-Button rechts. Mobile-Burger als alleiniges sichtbares Mobile-Element. Sticky-friendly mit border-bottom.",
    },
    "nav_centered_logo": {
        "category": "NAV",
        "label":    "Nav · Zentriertes Logo",
        "guidance": "Logo zentriert, je 2-3 Nav-Links links und rechts vom Logo. CTA als Button ganz rechts. Mobile: Logo bleibt zentriert, Burger links.",
    },
    "nav_minimal": {
        "category": "NAV",
        "label":    "Nav · Minimal",
        "guidance": "Nur Logo links + 1 primaerer CTA rechts. Keine Nav-Links. Fuer Landing-Pages mit klarer Single-Conversion.",
    },
    "nav_with_search": {
        "category": "NAV",
        "label":    "Nav · mit Suche",
        "guidance": "Logo links, Nav-Links + Such-Feld inline rechts daneben, CTA-Button rechts. Such-Feld mit Icon (lupe) als input.",
    },
    "nav_sidebar": {
        "category": "NAV",
        "label":    "Nav · Sidebar (vertikal)",
        "guidance": "Vertikale Sidebar-Nav: Logo oben, Nav-Links untereinander, CTA unten. Width fixed (w-60), full-height. Fuer App-Layouts.",
    },

    # ── LEIST / Feature-Sections ────────────────────────────────────────────
    "leist_split_left": {
        "category": "LEIST",
        "label":    "Leistung · Bild links + Text rechts",
        "guidance": "Zwei-Spalten 50/50: Bild-Placeholder links, rechts Headline + Subtext + Bullet-Liste mit Check-Icons (4-6 Punkte) + sekundaerer CTA.",
    },
    "leist_split_right": {
        "category": "LEIST",
        "label":    "Leistung · Bild rechts + Text links",
        "guidance": "Spiegelung von leist_split_left.",
    },
    "leist_3_col": {
        "category": "LEIST",
        "label":    "Leistung · 3-Spalten-Cards",
        "guidance": "Section-Headline zentriert. Darunter 3 Karten nebeneinander: jede Karte = Icon (SVG) + Titel + Beschreibung (2-3 Saetze) + 'Mehr erfahren'-Link. Mobile: gestapelt.",
    },
    "leist_4_col": {
        "category": "LEIST",
        "label":    "Leistung · 4-Spalten-Cards",
        "guidance": "Wie leist_3_col, aber 4 Karten nebeneinander. Mobile: 2x2 Grid, dann Single-Column.",
    },
    "leist_grid_cards_with_image": {
        "category": "LEIST",
        "label":    "Leistung · Grid mit Bild-Cards",
        "guidance": "3-Spalten-Grid, jede Karte hat oben einen Bild-Placeholder (aspect-video) und darunter Titel + Kurztext + Pfeil-Link.",
    },
    "leist_tabs": {
        "category": "LEIST",
        "label":    "Leistung · Tabs",
        "guidance": "Section mit Tab-Navigation oben (3-5 Tabs). Aktiver Tab unterstrichen. Darunter Tab-Inhalt (statisch im Wireframe — zeige nur den ersten Tab als ausgewaehlt). Tab-Inhalt: 50/50-Layout Text + Bild.",
    },
    "leist_overlapping": {
        "category": "LEIST",
        "label":    "Leistung · Overlapping Images",
        "guidance": "Zwei ueberlappende Bild-Placeholder (eines absolut positioniert, leicht versetzt). Rechts daneben Text-Block. Editorial-Look.",
    },
    "leist_alternating": {
        "category": "LEIST",
        "label":    "Leistung · Wechselnde Reihen",
        "guidance": "Drei aufeinanderfolgende Feature-Reihen: 1. Bild links/Text rechts, 2. Text links/Bild rechts, 3. Bild links/Text rechts. Jede Reihe hat eigene Headline + Subtext + Bullets.",
    },

    # ── TRUST / Social Proof ─────────────────────────────────────────────────
    "trust_testimonial_single": {
        "category": "TRUST",
        "label":    "Trust · Einzel-Testimonial",
        "guidance": "Eine grosse Testimonial-Karte zentriert. Zitat in serif-Font (text-2xl), darunter Avatar + Name + Position. Optional 5-Sterne-Rating ueber dem Zitat.",
    },
    "trust_testimonial_grid": {
        "category": "TRUST",
        "label":    "Trust · Testimonial-Grid (3)",
        "guidance": "Drei Testimonial-Karten nebeneinander. Jede: Zitat (kurz, 2-3 Saetze), Avatar, Name + Funktion, Sternchen-Rating.",
    },
    "trust_stats_row": {
        "category": "TRUST",
        "label":    "Trust · Zahlen-Reihe",
        "guidance": "4 Zahlen-Counter horizontal. Jede: grosse Zahl (text-5xl, fett), kurzes Label darunter (z.B. '500+ zufriedene Kunden'). Border zwischen Counters.",
    },
    "trust_logo_strip": {
        "category": "TRUST",
        "label":    "Trust · Logo-Streifen",
        "guidance": "Section mit kleiner Headline ('Wir arbeiten mit:'), darunter horizontale Reihe mit 6-8 Logo-Placeholdern (graue Rechtecke). Mobile: 2 Reihen a 3-4.",
    },
    "trust_team_grid": {
        "category": "TRUST",
        "label":    "Trust · Team-Grid",
        "guidance": "3-4 Team-Mitglieder als Karten: Avatar (rund) + Name + Position + 1-Satz-Bio. Optional Social-Links (Mail/LinkedIn) als Icons.",
    },
    "trust_fallstudien_3": {
        "category": "TRUST",
        "label":    "Trust · 3 Fallstudien",
        "guidance": "Drei Case-Study-Karten: jede mit Vorher/Nachher-Bild-Placeholder, Kunden-Name, kurzer Problem→Loesung-Text, Kennzahl als Highlight.",
    },
    "trust_comparison": {
        "category": "TRUST",
        "label":    "Trust · Vergleichstabelle",
        "guidance": "Tabelle mit 2-3 Spalten: 'Wir' vs 'Wettbewerb 1' vs 'Wettbewerb 2'. Zeilen sind Feature-Punkte mit Check/X-Icons.",
    },

    # ── SEO / Content ────────────────────────────────────────────────────────
    "seo_long_form": {
        "category": "SEO",
        "label":    "SEO · Lang-Text",
        "guidance": "Reine Text-Section, max-w-prose zentriert. H2-Headline, dann Paragraphen, H3-Subheadlines, mehr Paragraphen, Bullet-Liste, Inline-CTA-Box am Ende.",
    },
    "seo_with_toc": {
        "category": "SEO",
        "label":    "SEO · mit Inhaltsverzeichnis",
        "guidance": "Zwei-Spalten: links sticky Inhaltsverzeichnis (5-7 Anker-Links), rechts Long-Form-Content mit H2/H3-Struktur.",
    },
    "seo_blog_grid": {
        "category": "SEO",
        "label":    "SEO · Blog-Karten-Grid",
        "guidance": "Section-Headline + 3-Spalten-Grid mit Blog-Karten: Bild-Placeholder oben, Kategorie-Badge, Titel, Excerpt (2 Saetze), Datum + Autor.",
    },
    "seo_faq_simple": {
        "category": "SEO",
        "label":    "SEO · FAQ Akkordeon",
        "guidance": "Section-Headline zentriert. Darunter 8-10 FAQ-Items als statische Akkordeons (kein JS): Frage als button-styled-summary, Antwort darunter. Erstes Item geoeffnet.",
    },
    "seo_faq_categorized": {
        "category": "SEO",
        "label":    "SEO · FAQ kategorisiert",
        "guidance": "FAQ in 2-3 Spalten gruppiert nach Themen-Kategorien. Jede Spalte hat eigene Sub-Headline + 3-4 FAQ-Items.",
    },

    # ── CTA / Call-to-Action ─────────────────────────────────────────────────
    "cta_inline_strip": {
        "category": "CTA",
        "label":    "CTA · Inline-Streifen",
        "guidance": "Kompakter horizontaler Streifen: Headline links, primaerer Button rechts. Background gray-100, py-8.",
    },
    "cta_final_large": {
        "category": "CTA",
        "label":    "CTA · Grosse End-CTA",
        "guidance": "Volle Section py-20: zentrierte grosse Headline (text-4xl/5xl), 1-2 Saetze Subtext, zwei Buttons (primaer + sekundaer). Background bg-gray-900 mit text-white.",
    },
    "cta_urgency": {
        "category": "CTA",
        "label":    "CTA · Urgency / Stichtag",
        "guidance": "CTA mit prominentem Datum/Counter: 'Nur noch bis 31.12.' als Headline, Untertitel mit Foerder-Hinweis (z.B. BAFA), grosser CTA-Button.",
    },
    "cta_with_form": {
        "category": "CTA",
        "label":    "CTA · mit Mini-Formular",
        "guidance": "Headline + Subtext zentriert, darunter horizontales Mini-Formular: nur E-Mail-Feld + Submit-Button nebeneinander. Trust-Badges darunter klein.",
    },
    "cta_split_contact": {
        "category": "CTA",
        "label":    "CTA · Split (Form + Kontakt-Daten)",
        "guidance": "Zwei-Spalten: links Kontakt-Formular (4-5 Felder), rechts Kontakt-Daten (Adresse, Telefon, E-Mail) + Map-Placeholder.",
    },

    # ── HW / Hardware / Pricing ──────────────────────────────────────────────
    "hw_pricing_3_tier": {
        "category": "HW",
        "label":    "HW · 3-Pakete-Pricing",
        "guidance": "Drei Pricing-Karten nebeneinander. Mittlere ist hervorgehoben (border-2, shadow). Jede Karte: Paket-Name, Preis (gross), Feature-Liste mit Check-Icons (5-7 Items), CTA-Button.",
    },
    "hw_pricing_comparison": {
        "category": "HW",
        "label":    "HW · Pricing-Vergleichstabelle",
        "guidance": "Tabelle mit 3 Tier-Spalten + Feature-Zeilen. Erste Zeile zeigt Tier-Namen + Preise. Folgezeilen: Feature-Name + Check/X-Icons pro Tier.",
    },
    "hw_product_grid": {
        "category": "HW",
        "label":    "HW · Produkt-Grid",
        "guidance": "3-Spalten-Grid mit Produkt-Karten: Bild-Placeholder, Produkt-Name, Kurz-Spec, Preis, CTA-Button.",
    },
    "hw_product_detail": {
        "category": "HW",
        "label":    "HW · Produkt-Detail",
        "guidance": "Zwei-Spalten: links Produkt-Bild gross, rechts Produkt-Name + Preis + Feature-Liste + CTA-Button + Spec-Tabelle.",
    },

    # ── FOOT / Footer ────────────────────────────────────────────────────────
    "foot_4_col": {
        "category": "FOOT",
        "label":    "Footer · 4-Spalten",
        "guidance": "Klassischer Footer: Spalte 1 Logo + Tagline, Spalten 2-4 mit Link-Listen (Sitemap / Service / Rechtliches). Bottom-Bar mit Copyright + Social-Icons.",
    },
    "foot_compact": {
        "category": "FOOT",
        "label":    "Footer · Kompakt",
        "guidance": "Schmaler Footer: nur eine Reihe mit Logo links, ein paar wichtige Links zentriert, Social-Icons rechts. py-6.",
    },
    "foot_with_newsletter": {
        "category": "FOOT",
        "label":    "Footer · mit Newsletter",
        "guidance": "Top-Section: Newsletter-Anmeldung (Headline + E-Mail-Input + Submit). Bottom-Section: 4-Spalten-Layout wie foot_4_col.",
    },
    "foot_with_map": {
        "category": "FOOT",
        "label":    "Footer · mit Mini-Map",
        "guidance": "Zwei-Bereiche: oben links Map-Placeholder + Adresse, oben rechts Link-Liste. Bottom-Bar mit Copyright.",
    },

    # ── CUSTOM / Misc ────────────────────────────────────────────────────────
    "custom_banner_top": {
        "category": "CUSTOM",
        "label":    "Banner · Top-Streifen",
        "guidance": "Schmaler Banner ueber Nav: Text + Inline-CTA-Link, Schliessen-X rechts. Background bg-gray-900 text-white. py-2.",
    },
    "custom_cookie_consent": {
        "category": "CUSTOM",
        "label":    "Cookie-Consent",
        "guidance": "Sticky-Bottom-Card: Text-Block + 3 Buttons (Akzeptieren / Ablehnen / Einstellungen). Mit shadow-lg, border, rounded.",
    },
    "custom_breadcrumb": {
        "category": "CUSTOM",
        "label":    "Breadcrumb-Pfad",
        "guidance": "Horizontale Breadcrumb mit 3-4 Items, getrennt durch '>' oder '/'. Letztes Item ist die aktuelle Seite (text-gray-900), die anderen sind links.",
    },
    "custom_progress_steps": {
        "category": "CUSTOM",
        "label":    "Progress-Steps",
        "guidance": "Mehrstufiger Form-Indicator: 4-5 Schritte horizontal, jeder mit Nummer-Bubble + Label. Aktive Schritte gefuellt, kommende leer.",
    },
    "custom_timeline": {
        "category": "CUSTOM",
        "label":    "Timeline · Vertikal",
        "guidance": "Vertikale Timeline mit 5-6 Eintraegen. Linker Rand: Datum + Bullet-Marker auf vertikaler Linie. Rechts: Titel + Beschreibung pro Eintrag.",
    },
    "custom_gallery": {
        "category": "CUSTOM",
        "label":    "Galerie · Bild-Grid",
        "guidance": "3- oder 4-Spalten-Grid mit Bild-Placeholdern unterschiedlicher Aspect-Ratios (Masonry-aehnlich). Hover-Effekt auf Karten.",
    },
    "custom_404": {
        "category": "CUSTOM",
        "label":    "404 · Fehlerseite",
        "guidance": "Volle Section, zentriert: '404'-Heading sehr gross, 'Seite nicht gefunden'-Subhead, kurzer Text, zwei Buttons (Zur Startseite / Kontakt).",
    },
    "custom_coming_soon": {
        "category": "CUSTOM",
        "label":    "Coming Soon",
        "guidance": "Zentriertes Layout: 'Bald verfuegbar'-Headline, kurzer Subtext, Newsletter-Mini-Form, Countdown-Placeholder (statisch).",
    },
}


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


class _Abbruch(Exception):
    """Ein Grund, den Job mit einer verstaendlichen Meldung zu beenden."""


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


def _als_json(roh: str) -> dict:
    """Parst die Antwort. `strict=False` laesst rohe Steuerzeichen in
    Zeichenketten durch — ein Zeilenumbruch mitten im Markup ist der haeufigste
    Ausrutscher und kein Grund, eine Minute Rechenzeit wegzuwerfen."""
    ergebnis = json.loads(roh, strict=False)
    if not isinstance(ergebnis, dict):
        raise _Abbruch("KI-Output ist kein Object")
    return ergebnis


def _json_nachbesserung(exc: json.JSONDecodeError) -> str:
    return f"""Deine Antwort war kein gueltiges JSON: {exc.msg} (Zeichen {exc.pos}).

Sende denselben Block noch einmal, diesmal als striktes JSON. Achte besonders
darauf, dass Anfuehrungszeichen im HTML mit \\" escaped sind und dass kein
Zeilenumbruch unescaped in einer Zeichenkette steht.
Antworte AUSSCHLIESSLICH mit dem JSON — kein Markdown-Wrapper, keine Erklaerung."""


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


# ─────────────────────────────────────────────────────────────────────────────
# Wireframe pro Projekt: Read / manueller Save / KI-Generator
# ─────────────────────────────────────────────────────────────────────────────

# Vorgabe am Router, nicht an der einzelnen Route. Bis zum 21.08.2026 trugen
# diese Routen nur `require_any_auth` und **keine Zeilenpruefung**: Sie holen
# das Projekt per `project_id` und antworten. Kunden haben Konten — ein
# angemeldeter Kunde kam damit an **jedes** Projekt (Naht `/api/projects`,
# `docs/module-karte.md`; dieselbe Bauart wie L-66).
#
# Alle Aufrufer haengen an `roles={{'admin', 'auditor'}}`, also am Innendienst.
# Die Sperre stand in der Oberflaeche statt am Endpunkt — und eine
# Oberflaechenpruefung ist keine Sperre.
wireframe_router = APIRouter(prefix="/api/projects", tags=["wireframe"],
                              dependencies=[Depends(require_innendienst)])


class WireframeBlock(BaseModel):
    slug: str
    order: int = 0
    slots: dict = {}
    # Stufe B: Markup, das nur für diesen Kunden gilt. Ist es gesetzt, zieht der
    # Renderer es dem Bibliotheks-Template vor. Der Block bleibt trotzdem
    # derselbe — `slug` zeigt weiter auf die Vorlage, aus der er entstanden ist,
    # und die Slot-Angaben kommen unverändert von dort.
    html_override: Optional[str] = None


class WireframePage(BaseModel):
    page_id: int
    page_name: Optional[str] = None
    blocks: list[WireframeBlock] = []


def _pruefe_variante(db: Session, block) -> dict:
    """Der Vertragsbefund einer kundeneigenen Variante.

    Zwei Dinge zusaetzlich zum Vertrag:

    * Die Variante wird gegen den **Slug ihres Bibliotheksblocks** geprueft.
      Traegt sie eine fremde Markierung, findet der Editor den Block nicht
      wieder (Regel R2).
    * Sie darf die Slots **nicht umbenennen**. `generate-copy` und der
      Slot-Editor lesen die Angaben des Bibliotheksblocks; erfindet die Variante
      eigene Schluessel, fuellt sie niemand mehr. Weglassen ist erlaubt — eine
      kuerzere Fassung ist eine Gestaltungsentscheidung.
    """
    vorlage = (db.query(ComponentLibrary)
                 .filter(ComponentLibrary.slug == block.slug).first())
    slots = (vorlage.slots if vorlage else None) or []
    bekannt = {s.get("key") for s in slots if isinstance(s, dict)}

    verstoesse = [{"regel": v.regel, "text": v.text}
                  for v in pruefe(block.html_override, slug=block.slug)]

    if vorlage is None:
        verstoesse.append({
            "regel": "B1",
            "text": f"Zu '{block.slug}' gibt es keinen Bibliotheksblock — eine "
                    f"Variante braucht die Vorlage, aus der sie entstanden ist.",
        })
    else:
        for name in slots_im_markup(block.html_override):
            if name not in bekannt:
                verstoesse.append({
                    "regel": "B2",
                    "text": f'Slot "{name}" steht nur in der Variante. Die '
                            f"Slot-Angaben kommen vom Bibliotheksblock — "
                            f"generate-copy wuerde ihn nie fuellen.",
                })

    return {"konform": not verstoesse, "verstoesse": verstoesse}


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
    """Manueller Save (Block-Tausch im UI, ohne KI).

    Kundeneigene Varianten (`html_override`) gehen durch dasselbe Tor wie die
    Bibliothek: Was den Vertrag verletzt, wird nicht gespeichert. Sonst waere
    er in einer Zeile zu umgehen — man schriebe den Block einfach nicht in die
    Bibliothek, sondern direkt beim Kunden.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    for seite in data.pages:
        for block in seite.blocks:
            if not (block.html_override or "").strip():
                continue
            befund = _pruefe_variante(db, block)
            if befund["verstoesse"]:
                raise HTTPException(422, {
                    "message": f"Die Variante von '{block.slug}' verletzt den "
                               f"Vertrag und wurde nicht gespeichert.",
                    "slug": block.slug,
                    "page_id": seite.page_id,
                    **befund,
                })

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
# Stufe B: einen Block fuer diesen Kunden umschreiben
# ─────────────────────────────────────────────────────────────────────────────

class VarianteRequest(BaseModel):
    page_id: int
    slug:    str
    wunsch:  Optional[str] = ""


@wireframe_router.get("/wireframe-variant-jobs/{job_id}")
def get_variant_job(job_id: str, user=Depends(require_any_auth)):
    """Polling fuer den Varianten-Auftrag. Cleanup nach dem ersten Abholen."""
    job = _variant_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        return _variant_jobs.pop(job_id)
    return job


@wireframe_router.post("/{project_id}/wireframe/variant")
def generate_variant(
    project_id: int,
    body: VarianteRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Startet das Umschreiben eines Blocks fuer diesen Kunden.

    Returnt sofort `{job_id, status: 'running'}` — das Frontend pollt
    `GET /api/projects/wireframe-variant-jobs/{job_id}`.

    Gespeichert wird hier nichts: Das Ergebnis geht zurueck ans Frontend, und
    erst der Save des Wireframes traegt es ein — durch dasselbe Tor wie jede
    andere Variante.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Projekt nicht gefunden")
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    vorlage = (db.query(ComponentLibrary)
                 .filter(ComponentLibrary.slug == body.slug).first())
    if not vorlage:
        raise HTTPException(404, f"Bibliotheksblock '{body.slug}' nicht gefunden")

    briefing = (db.query(Briefing).filter(Briefing.lead_id == proj.lead_id).first()
                if proj.lead_id else None)
    seite = _seiten_name(proj.wireframe_data, body.page_id)

    job_id = str(uuid.uuid4())
    _variant_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_variant_job,
        kwargs={
            "job_id":   job_id,
            "api_key":  api_key,
            "slug":     body.slug,
            "vorlage":  vorlage.html_template or "",
            "slots":    vorlage.slots or [],
            "briefing": briefing,
            "wunsch":   body.wunsch or "",
            "seite":    seite,
        },
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}


def _seiten_name(wireframe_data, page_id: int) -> str:
    for seite in (wireframe_data or {}).get("pages", []):
        if seite.get("page_id") == page_id:
            return seite.get("page_name") or ""
    return ""


def _run_variant_job(*, job_id, api_key, slug, vorlage, slots, briefing,
                     wunsch, seite) -> None:
    """Hintergrund-Thread: schreibt den Block um und prueft das Ergebnis."""
    try:
        client = Anthropic(api_key=api_key)
        ergebnis = erzeuge_variante(
            ki_runde=_ki_runde, client=client, slug=slug, vorlage=vorlage,
            slots=slots, briefing=briefing, wunsch=wunsch, seite=seite,
            auftrag=job_id,
        )
        _variant_jobs[job_id] = {"status": "done", "result": ergebnis}
    except (VariantenAbbruch, _Abbruch) as exc:
        _variant_jobs[job_id] = {"status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.error("variant job %s crashed: %s", job_id, exc, exc_info=True)
        _variant_jobs[job_id] = {"status": "error", "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Stufe C: die Seite komponieren
# ─────────────────────────────────────────────────────────────────────────────

class KompositionRequest(BaseModel):
    page_id: int


@wireframe_router.get("/wireframe-compose-jobs/{job_id}")
def get_compose_job(job_id: str, user=Depends(require_any_auth)):
    """Polling fuer den Kompositions-Auftrag."""
    job = _compose_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        return _compose_jobs.pop(job_id)
    return job


@wireframe_router.post("/{project_id}/wireframe/compose")
def compose_page(
    project_id: int,
    body: KompositionRequest,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Schlaegt eine Abfolge fuer diese Seite vor.

    Gespeichert wird nichts: Das Ergebnis geht ans Frontend, dort wird es
    angesehen und uebernommen. Das Markup je Section schreibt danach Stufe B.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Projekt nicht gefunden")
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    # Nur freigegebene Bloecke — ein Entwurf hat auf einer Kundenseite nichts
    # verloren, und der Wireframe-Generator haelt es genauso.
    bloecke = [
        {"slug": r.slug, "category": r.category, "name": r.name,
         "ki_prompt_hint": r.ki_prompt_hint}
        for r in _nur_freigegebene(db.query(ComponentLibrary)).all()
    ]

    seite = db.execute(text("""
        SELECT page_name, zweck, position FROM sitemap_pages WHERE id = :pid
    """), {"pid": body.page_id}).fetchone()
    seiten_name = (seite[0] if seite else "") or _seiten_name(
        proj.wireframe_data, body.page_id) or "Seite"
    zweck = (seite[1] if seite else "") or ""
    ist_startseite = bool(seite and (seite[2] or 0) == 0)

    bestehend = [b.get("slug") for b in _bloecke_der_seite(proj.wireframe_data,
                                                           body.page_id)]

    briefing = (db.query(Briefing).filter(Briefing.lead_id == proj.lead_id).first()
                if proj.lead_id else None)

    job_id = str(uuid.uuid4())
    _compose_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_compose_job,
        kwargs={
            "job_id": job_id, "api_key": api_key, "seite": seiten_name,
            "zweck": zweck, "ist_startseite": ist_startseite, "briefing": briefing,
            "bloecke": bloecke, "bestehend": bestehend,
        },
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}


def _bloecke_der_seite(wireframe_data, page_id: int) -> list:
    for seite in (wireframe_data or {}).get("pages", []):
        if seite.get("page_id") == page_id:
            return sorted(seite.get("blocks", []), key=lambda b: b.get("order", 0))
    return []


def _run_compose_job(*, job_id, api_key, seite, zweck, ist_startseite, briefing,
                     bloecke, bestehend) -> None:
    """Hintergrund-Thread: schlaegt die Abfolge vor und prueft sie."""
    try:
        client = Anthropic(api_key=api_key)
        ergebnis = komponiere(
            ki_runde=_ki_runde, client=client, seite=seite, zweck=zweck,
            ist_startseite=ist_startseite, briefing=briefing, bloecke=bloecke,
            bestehend=bestehend, auftrag=job_id)
        # Namen dazu, damit das Frontend die Abfolge lesbar anzeigen kann.
        nach_slug = {b["slug"]: b for b in bloecke}
        for section in ergebnis["sections"]:
            eintrag = nach_slug.get(section["slug"]) or {}
            section["name"] = eintrag.get("name") or section["slug"]
            section["category"] = eintrag.get("category") or ""
        _compose_jobs[job_id] = {"status": "done", "result": ergebnis}
    except (KompositionsAbbruch, _Abbruch) as exc:
        _compose_jobs[job_id] = {"status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.error("compose job %s crashed: %s", job_id, exc, exc_info=True)
        _compose_jobs[job_id] = {"status": "error", "error": str(exc)}


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

        # Nur Freigegebenes. Ein Entwurf darf nie auf einer Kundenseite landen.
        components_rows = _nur_freigegebene(db.query(ComponentLibrary)).all()
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
        #
        # Streaming-Pflicht ab 2025: Die Anthropic-SDK weigert sich, non-streaming
        # Calls mit hoher max_tokens-Erwartung > ~10min zu starten und wirft
        # ValueError("Streaming is required..."). Daher hier ueber stream() —
        # final_message hat dieselbe Struktur wie ein gewoehnliches Response.
        with client.messages.stream(
            model="claude-sonnet-5", thinking={"type": "disabled"},
            max_tokens=32000,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            # Iterator konsumieren, damit der Akkumulator das final_message baut.
            for _ in stream.text_stream:
                pass
            response = stream.get_final_message()
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
            # strict=False wie im Block-Generator: rohe Steuerzeichen in
            # Zeichenketten sollen einen Auftrag nicht kosten. Eine zweite
            # Chance wie dort gibt es hier bewusst noch nicht — dafuer fehlt
            # der Beleg, und dieser Auftrag ist deutlich teurer zu wiederholen.
            wireframe = json.loads(raw_text, strict=False)
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
