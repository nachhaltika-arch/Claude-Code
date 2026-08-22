"""
Brand Design API
GET  /api/branddesign/{lead_id}                    - Get all stored brand data
POST /api/branddesign/{lead_id}/scrape             - Scrape website for brand colors/fonts/logo
POST /api/branddesign/{lead_id}/analyze-screenshot - Claude Vision analysis of screenshot
POST /api/branddesign/{lead_id}/upload-pdf         - Upload brand PDF (multipart)
GET  /api/branddesign/{lead_id}/pdf                - Download brand PDF
GET  /api/branddesign/{lead_id}/guideline          - Load saved brand guideline
POST /api/branddesign/{lead_id}/guideline/generate - Generate brand guideline via AI
PUT  /api/branddesign/{lead_id}/guideline          - Save manual edits to guideline
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from routers.auth_router import require_innendienst
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Lead, Briefing
import httpx, re, os, json, anthropic, logging
from datetime import datetime
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/branddesign", tags=["branddesign"],
                   dependencies=[Depends(require_innendienst)])


# ── Utility ───────────────────────────────────────────────────────────────────

def _set(obj, attr: str, value) -> None:
    """setattr only if the column exists on the ORM object (migration-safe)."""
    try:
        setattr(obj, attr, value)
    except Exception:
        pass




# ── Endpoint 1 — GET brand data ───────────────────────────────────────────────

@router.get("/{lead_id}")
def get_brand_data(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    def _j(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    design_json = getattr(lead, 'brand_design_json', None)
    design_data = None
    if design_json:
        try:
            design_data = json.loads(design_json)
        except Exception:
            pass

    design_tokens = None
    raw_tokens = getattr(lead, 'brand_design_tokens_json', None)
    if raw_tokens:
        try:
            design_tokens = json.loads(raw_tokens)
        except Exception:
            pass

    fonts_detail = None
    raw_fd = getattr(lead, 'brand_fonts_detail', None)
    if raw_fd:
        try: fonts_detail = json.loads(raw_fd)
        except Exception: pass

    return {
        "lead_id":         lead_id,
        "primary_color":   lead.brand_primary_color,
        "secondary_color": lead.brand_secondary_color,
        "font_primary":    lead.brand_font_primary,
        "font_secondary":  lead.brand_font_secondary,
        "font_heading":    getattr(lead, 'brand_font_heading', None) or lead.brand_font_primary,
        "font_body":       getattr(lead, 'brand_font_body',    None) or lead.brand_font_secondary,
        "font_accent":     getattr(lead, 'brand_font_accent',  None),
        "logo_url":        lead.brand_logo_url,
        "all_colors":      _j(lead.brand_colors),
        "all_fonts":       _j(lead.brand_fonts),
        "scrape_failed":   bool(lead.brand_scrape_failed or False),
        "design_style":    lead.brand_design_style,
        "brand_notes":     lead.brand_notes,
        "pdf_filename":    lead.brand_pdf_filename,
        "scraped_at":      str(lead.brand_scraped_at or '')[:16] or None,
        "ga_status":         lead.ga_status or 'unbekannt',
        "ga_type":           lead.ga_type,
        "ga_measurement_id": lead.ga_measurement_id,
        "ga_checked_at":     str(lead.ga_checked_at or '')[:16] or None,
        "design_data":       design_data,
        "design_tokens":     design_tokens,
        "fonts_detail":      fonts_detail,
        "guideline_generated": bool(getattr(lead, 'brand_guideline_generated_at', None)),
        "guideline_generated_at": str(getattr(lead, 'brand_guideline_generated_at', '') or '')[:16] or None,
    }


# ── Endpoint 1b — Manual save ─────────────────────────────────────────────────

@router.put("/{lead_id}")
def update_brand_design(lead_id: int, body: dict, db: Session = Depends(get_db)):
    """Manuelle Branddesign-Felder speichern."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    mapping = {
        "primary_color":   "brand_primary_color",
        "secondary_color": "brand_secondary_color",
        "font_primary":    "brand_font_primary",
        "font_secondary":  "brand_font_secondary",
        "font_heading":    "brand_font_heading",
        "font_body":       "brand_font_body",
        "font_accent":     "brand_font_accent",
        "design_style":    "brand_design_style",
        "brand_notes":     "brand_notes",
        "logo_url":        "brand_logo_url",
    }
    updated = []
    for body_field, lead_attr in mapping.items():
        if body_field in body:
            _set(lead, lead_attr, body[body_field])
            updated.append(body_field)

    if "design_tokens" in body:
        tokens = body["design_tokens"]
        _set(lead, 'brand_design_tokens_json',
             json.dumps(tokens, ensure_ascii=False) if isinstance(tokens, dict) else tokens)
        updated.append("design_tokens")
        if isinstance(tokens, dict):
            if tokens.get("primary"):    _set(lead, 'brand_primary_color',  tokens["primary"])
            if tokens.get("secondary"):  _set(lead, 'brand_secondary_color', tokens["secondary"])
            if tokens.get("font_h1"):    _set(lead, 'brand_font_heading', tokens["font_h1"])
            if tokens.get("font_body"):  _set(lead, 'brand_font_body',    tokens["font_body"])
            if tokens.get("font_akzent"):_set(lead, 'brand_font_accent',  tokens["font_akzent"])

    if updated:
        _set(lead, 'brand_scraped_at', datetime.utcnow())
        db.commit()
    return {"saved": True, "updated_fields": updated}


# ── Endpoint 1c — Font suggestions ────────────────────────────────────────────







# ── Endpoint 2 — Scrape ────────────────────────────────────────────────────────



# ── Endpoint 3 — Vision analysis ──────────────────────────────────────────────



# ── Endpoint 4 — Upload PDF ────────────────────────────────────────────────────



# ── Endpoint 5 — Download PDF ─────────────────────────────────────────────────



# ── Endpoint 6 — Check Google Analytics ──────────────────────────────────────



# ── Brand Guideline ────────────────────────────────────────────────────────────





