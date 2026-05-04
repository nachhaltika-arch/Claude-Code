"""
Website Template Library
POST   /api/website-templates/import        - Single ZIP upload
POST   /api/website-templates/import-bulk   - Multiple ZIPs at once
GET    /api/website-templates/              - List (filter: category, gewerk, style)
GET    /api/website-templates/{id}/preview  - HTML preview (iframe-safe)
PUT    /api/website-templates/{id}          - Update metadata / tags
DELETE /api/website-templates/{id}          - Delete
GET    /api/website-templates/suggestions   - Inspiration URL suggestions per trade

Uses the existing website_templates table which has html_content, css_content,
grapes_data (JSONB). Mapped in this router as html, css, gjs_data for
consistency with the spec.
"""
import io
import json
import logging
import re
import zipfile
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/website-templates", tags=["website-templates"])


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_slug(name: str) -> str:
    s = (name or "").lower().strip()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:200] or "template"


def _unique_slug(base: str, db: Session) -> str:
    slug = base
    counter = 2
    while db.execute(
        text("SELECT id FROM website_templates WHERE slug = :s"), {"s": slug}
    ).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _extract_from_zip(zip_bytes: bytes, filename: str) -> dict:
    """Extracts HTML/CSS or GrapesJS JSON from a ZIP archive."""
    result = {
        "name": (filename or "template").replace(".zip", ""),
        "html": "",
        "css": "",
        "gjs_data": None,
    }
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            files = zf.namelist()

            # Prefer GrapesJS JSON
            gjs_file = next(
                (f for f in files
                 if f.endswith(".grapesjs") or f.endswith("grapesjs.json")
                 or f.endswith("gjs.json")),
                None,
            )
            if gjs_file:
                try:
                    result["gjs_data"] = zf.read(gjs_file).decode("utf-8", errors="ignore")
                    gjs = json.loads(result["gjs_data"])
                    pages = gjs.get("pages") or []
                    if pages:
                        comps = pages[0].get("frames", [{}])[0].get("component", {})
                        if isinstance(comps, dict):
                            inner = comps.get("components", "")
                            if isinstance(inner, str):
                                result["html"] = inner
                except Exception:
                    pass
                return result

            # HTML/CSS fallback
            html_file = next(
                (f for f in files if f.endswith("index.html")),
                next((f for f in files if f.endswith(".html")), None),
            )
            css_file = next(
                (f for f in files if f.endswith("style.css") or f.endswith("main.css")),
                next((f for f in files if f.endswith(".css")), None),
            )

            if html_file:
                raw_html = zf.read(html_file).decode("utf-8", errors="ignore")
                body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", raw_html, re.I)
                result["html"] = body_match.group(1).strip() if body_match else raw_html

                if css_file:
                    result["css"] = zf.read(css_file).decode("utf-8", errors="ignore")
                else:
                    # Inline <style> tags
                    styles = re.findall(r"<style[^>]*>([\s\S]*?)</style>", raw_html, re.I)
                    result["css"] = "\n".join(styles)

    except zipfile.BadZipFile:
        result["error"] = "Keine gültige ZIP-Datei"
    except Exception as e:
        result["error"] = str(e)
    return result


def _row_to_dict(r):
    """Map DB row to dict with normalized field names."""
    d = dict(r._mapping)
    # Normalize legacy ↔ new names
    d["html"] = d.pop("html_content", None) or ""
    d["css"]  = d.pop("css_content", None) or ""
    d["gjs_data"] = d.pop("grapes_data", None)
    return d


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/import")
async def import_template(
    file: UploadFile = File(...),
    name: str = Form(""),
    category: str = Form("allgemein"),
    style_tags: str = Form("[]"),
    gewerk_tags: str = Form('["alle"]'),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Einzelne ZIP-Datei als Template importieren."""
    content = await file.read()
    extracted = _extract_from_zip(content, file.filename or "template")
    if extracted.get("error"):
        raise HTTPException(status_code=400, detail=f"ZIP-Fehler: {extracted['error']}")

    tpl_name = (name or extracted["name"]).strip()
    slug = _unique_slug(_make_slug(tpl_name), db)

    db.execute(text("""
        INSERT INTO website_templates
          (name, slug, category, style_tags, gewerk_tags,
           html_content, css_content, grapes_data, source_file, source)
        VALUES
          (:name, :slug, :category, :style_tags, :gewerk_tags,
           :html, :css, CAST(:gjs AS JSONB), :source_file, 'upload')
    """), {
        "name":        tpl_name,
        "slug":        slug,
        "category":    category,
        "style_tags":  style_tags,
        "gewerk_tags": gewerk_tags,
        "html":        extracted.get("html", ""),
        "css":         extracted.get("css", ""),
        "gjs":         extracted.get("gjs_data"),
        "source_file": file.filename,
    })
    db.commit()
    return {"slug": slug, "name": tpl_name, "imported": True}


@router.post("/import-bulk")
async def import_bulk(
    files: List[UploadFile] = File(...),
    category: str = Form("allgemein"),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Mehrere ZIP-Dateien gleichzeitig importieren."""
    results = []
    for f in files:
        try:
            content = await f.read()
            extracted = _extract_from_zip(content, f.filename or "")
            if extracted.get("error"):
                results.append({"file": f.filename, "error": extracted["error"], "ok": False})
                continue

            slug = _unique_slug(_make_slug(extracted["name"]), db)
            db.execute(text("""
                INSERT INTO website_templates
                  (name, slug, category, html_content, css_content,
                   grapes_data, source_file, gewerk_tags, source)
                VALUES
                  (:name, :slug, :category, :html, :css,
                   CAST(:gjs AS JSONB), :source_file, '["alle"]', 'upload')
            """), {
                "name":        extracted["name"],
                "slug":        slug,
                "category":    category,
                "html":        extracted.get("html", ""),
                "css":         extracted.get("css", ""),
                "gjs":         extracted.get("gjs_data"),
                "source_file": f.filename,
            })
            results.append({"file": f.filename, "slug": slug, "ok": True})
        except Exception as e:
            logger.warning(f"Template import {f.filename} failed: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            results.append({"file": f.filename, "error": str(e), "ok": False})

    db.commit()
    return {
        "imported": len([r for r in results if r.get("ok")]),
        "failed":   len([r for r in results if not r.get("ok")]),
        "results":  results,
    }


@router.get("/")
def list_templates(
    category: Optional[str] = None,
    gewerk: Optional[str] = None,
    style: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Alle Templates — gefiltert nach Kategorie/Gewerk/Stil."""
    where = ["COALESCE(is_active, TRUE) = TRUE"]
    params = {}
    if category:
        where.append("category = :category")
        params["category"] = category
    if gewerk:
        where.append("(gewerk_tags ILIKE :gewerk OR gewerk_tags ILIKE '%alle%')")
        params["gewerk"] = f"%{gewerk}%"
    if style:
        where.append("style_tags ILIKE :style")
        params["style"] = f"%{style}%"

    rows = db.execute(text(f"""
        SELECT id, name, slug, category, style_tags, gewerk_tags,
               thumbnail_url, sort_order, source_file, created_at
        FROM website_templates
        WHERE {' AND '.join(where)}
        ORDER BY sort_order NULLS LAST, name
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/suggestions")
def inspiration_suggestions(gewerk: Optional[str] = None):
    """Statische Liste guter Referenz-Websites pro Gewerk."""
    suggestions = {
        "sanitaer": [
            "https://www.breunig-sanitaer.de",
            "https://www.wolff-heizung-sanitaer.de",
            "https://www.meier-haustechnik.de",
        ],
        "heizung": [
            "https://www.buderus.de",
            "https://www.vaillant.de",
            "https://www.wolff-heizung-sanitaer.de",
        ],
        "elektro": [
            "https://www.elektro-schmid.de",
            "https://www.elektro-franke.de",
            "https://www.elektro-koerner.de",
        ],
        "maler": [
            "https://www.maler-heyse.de",
            "https://www.malerkronenberg.de",
            "https://www.malerbetrieb-muenchen.de",
        ],
        "dachdecker": [
            "https://www.dachdecker-seifert.de",
            "https://www.dachdecker-wiesbaden.de",
            "https://www.dachdecker-berlin.de",
        ],
        "schreiner": [
            "https://www.schreinerei-lang.de",
            "https://www.schreinerei-gebele.de",
        ],
        "fliesenleger": [
            "https://www.fliesen-koch.de",
            "https://www.fliesen-meyer.de",
        ],
    }
    key = (gewerk or "").lower()
    for k in suggestions:
        if k in key:
            return {"gewerk": k, "suggestions": suggestions[k]}
    # Fallback
    return {
        "gewerk": "allgemein",
        "suggestions": [
            "https://www.handwerker-muster.de",
            "https://www.handwerksmeister-beispiel.de",
            "https://www.qualitaets-handwerk.de",
        ],
    }


@router.get("/{template_id}/preview", response_class=HTMLResponse)
def get_preview(template_id: int, db: Session = Depends(get_db)):
    """HTML-Vorschau eines Templates — iframe-safe."""
    row = db.execute(
        text("SELECT html_content, css_content FROM website_templates WHERE id=:id"),
        {"id": template_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Template nicht gefunden")

    html = row.html_content or ""
    css  = row.css_content or ""

    full = f"""<!DOCTYPE html>
<html lang="de"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{css}</style>
</head><body>{html}</body></html>"""
    return HTMLResponse(content=full)


@router.put("/{template_id}")
def update_template(
    template_id: int,
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Template-Metadaten aktualisieren."""
    allowed = [
        "name", "category", "style_tags", "gewerk_tags",
        "thumbnail_url", "sort_order", "is_active", "description",
    ]
    fields = []
    params = {"id": template_id}
    for k in allowed:
        if k in data:
            fields.append(f"{k} = :{k}")
            params[k] = data[k]
    if fields:
        fields.append("updated_at = NOW()")
        db.execute(
            text(f"UPDATE website_templates SET {', '.join(fields)} WHERE id = :id"),
            params,
        )
        db.commit()
    return {"updated": template_id}


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    db.execute(text("DELETE FROM website_templates WHERE id = :id"), {"id": template_id})
    db.commit()
    return {"deleted": template_id}
