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

# Die Datenbloecke stehen seit dem 22.08.2026 in einer eigenen Datei
# (L-25): 398 Zeilen reine Daten, die zwischen den Routen lagen.
from routers.component_library_daten import (
    _ELEMENT_LABELS,
    _INDUSTRIES,
    _LAYOUT_PRESETS,
    _WIREFRAME_CONSTRAINTS,
)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)



# Separater Job-Store fuer den Component-Designer (KI-Komponenten-Generator).
# { job_id: { "status": "running"|"done"|"error", "result": dict|None, "error": str|None } }
_component_gen_jobs: dict = {}




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






# ── Generator-Logik (Background-Thread) ──────────────────────────────────────













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







class _Abbruch(Exception):
    """Ein Grund, den Job mit einer verstaendlichen Meldung zu beenden."""


















# ─────────────────────────────────────────────────────────────────────────────
# Wireframe pro Projekt: Read / manueller Save / KI-Generator
# ─────────────────────────────────────────────────────────────────────────────



















# ─────────────────────────────────────────────────────────────────────────────
# Stufe B: einen Block fuer diesen Kunden umschreiben
# ─────────────────────────────────────────────────────────────────────────────











# ─────────────────────────────────────────────────────────────────────────────
# Stufe C: die Seite komponieren
# ─────────────────────────────────────────────────────────────────────────────











# ─────────────────────────────────────────────────────────────────────────────
# KI-Generator-Logik (Background-Thread)
# ─────────────────────────────────────────────────────────────────────────────





