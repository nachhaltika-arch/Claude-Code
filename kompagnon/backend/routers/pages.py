"""
Seiten-Manager Router — verwaltet öffentliche Seiten (public_pages)
+ GrapesJS-Templates (page_templates).

WICHTIG: sitemap.py registriert bereits einen pages_router unter /api/pages
mit /{page_id}/editor für Sitemap-Seiten (Projekt-Builder).
Dieser Router ergänzt um:
  - /        (list / create)
  - /{id}    (get / save / delete)
  - /{id}/link-product
  - /templates/list
  - /templates/{id}
  - /templates/upload
  - /templates/{id}  (delete)

Die Pfad-Typen (int vs. String "templates") verhindern Kollisionen
mit den sitemap-Routen.
"""
import io
import json
import logging
import zipfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pages", tags=["public-pages"])


# ── TEMPLATES (zuerst, damit /templates/... nicht von /{page_id} gefressen wird) ──

@router.get("/templates/list")
def list_templates(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = db.execute(text(
        "SELECT id, name, description, category, thumbnail_url, is_builtin, created_at"
        "  FROM page_templates"
        " ORDER BY is_builtin DESC, sort_order, name"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(
        text("SELECT * FROM page_templates WHERE id=:id"),
        {"id": template_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Template nicht gefunden")
    return dict(row._mapping)


@router.post("/templates/upload")
async def upload_template(
    name: str = Form(...),
    category: str = Form("allgemein"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Akzeptiert:
      - .grapesjs  → direkt als GrapesJS-Projektdaten speichern
      - .zip       → .grapesjs aus ZIP oder index.html + style.css extrahieren
    """
    content = await file.read()
    filename = file.filename or ""
    ext = filename.split(".")[-1].lower()

    gjs_data: dict = {}
    html_content = ""
    css_content = ""

    if ext == "grapesjs":
        try:
            gjs_data = json.loads(content.decode("utf-8"))
        except Exception:
            raise HTTPException(400, "Ungültige .grapesjs-Datei")
    elif ext == "zip":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                files = zf.namelist()
                gjs_file = next(
                    (f for f in files if f.endswith(".grapesjs") or f.endswith("grapesjs.json")),
                    None,
                )
                if gjs_file:
                    gjs_data = json.loads(zf.read(gjs_file).decode("utf-8"))
                else:
                    html_file = next((f for f in files if f.endswith("index.html")), None)
                    css_file = next((f for f in files if f.endswith("style.css")), None)
                    if html_file:
                        html_content = zf.read(html_file).decode("utf-8", errors="replace")
                    if css_file:
                        css_content = zf.read(css_file).decode("utf-8", errors="replace")
        except zipfile.BadZipFile:
            raise HTTPException(400, "Ungültige ZIP-Datei")
    else:
        raise HTTPException(400, "Nur .zip und .grapesjs werden unterstützt")

    result = db.execute(text("""
        INSERT INTO page_templates
          (name, category, grapesjs_data, html_content, css_content)
        VALUES (:name, :cat, :gjs, :html, :css)
        RETURNING id
    """), {
        "name": name,
        "cat": category,
        "gjs": json.dumps(gjs_data),
        "html": html_content,
        "css": css_content,
    })
    new_id = result.fetchone()[0]
    db.commit()
    return {"id": new_id, "name": name}


@router.put("/templates/{template_id}")
def save_template(
    template_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Speichert GrapesJS-Daten, HTML, CSS und Meta-Infos eines Templates.
    Alle Felder optional — nur übergebene werden aktualisiert."""
    row = db.execute(
        text("SELECT is_builtin FROM page_templates WHERE id=:id"),
        {"id": template_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Template nicht gefunden")
    if row.is_builtin:
        raise HTTPException(400, "Eingebaute Templates können nicht bearbeitet werden")

    updates = []
    params = {"id": template_id}

    if "grapesjs_data" in body:
        updates.append("grapesjs_data = :gjs")
        params["gjs"] = json.dumps(body.get("grapesjs_data") or {})
    if "html_content" in body:
        updates.append("html_content = :html")
        params["html"] = body.get("html_content") or ""
    if "css_content" in body:
        updates.append("css_content = :css")
        params["css"] = body.get("css_content") or ""
    if "name" in body:
        updates.append("name = :name")
        params["name"] = (body.get("name") or "").strip() or "Unbenannt"
    if "category" in body:
        updates.append("category = :cat")
        params["cat"] = body.get("category") or "allgemein"
    if "description" in body:
        updates.append("description = :desc")
        params["desc"] = body.get("description") or ""
    if "thumbnail_url" in body:
        updates.append("thumbnail_url = :thumb")
        params["thumb"] = body.get("thumbnail_url") or ""

    if not updates:
        return {"success": True, "changed": 0}

    sql = f"UPDATE page_templates SET {', '.join(updates)} WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    return {"success": True, "changed": len(updates)}


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(
        text("SELECT is_builtin FROM page_templates WHERE id=:id"),
        {"id": template_id},
    ).fetchone()
    if row and row.is_builtin:
        raise HTTPException(400, "Eingebaute Templates können nicht gelöscht werden")
    db.execute(text("DELETE FROM page_templates WHERE id=:id"), {"id": template_id})
    db.commit()
    return {"success": True}


# ── PUBLIC PAGES ──────────────────────────────────────────────

@router.get("/")
def list_pages(
    page_type: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns public pages with pagination.

    Query params:
      page_type — filter by type (optional)
      limit     — max entries (default 200, max 500)
      offset    — skip N entries

    Response: {total, limit, offset, items[]}
    HTML/GrapesJS content is excluded from the list — fetch /api/pages/{id} for full data.
    """
    limit  = min(max(limit, 1), 500)
    offset = max(offset, 0)

    base_filter = ""
    params: dict = {}
    if page_type:
        base_filter = " WHERE page_type = :type"
        params["type"] = page_type

    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM public_pages{base_filter}"),
        params,
    ).fetchone()
    total = count_row[0] if count_row else 0

    params["limit"]  = limit
    params["offset"] = offset
    rows = db.execute(
        text(
            f"SELECT id, name, slug, page_type, meta_title, meta_description,"
            f"       is_published, created_at, updated_at"
            f"  FROM public_pages{base_filter}"
            f" ORDER BY page_type, name"
            f" LIMIT :limit OFFSET :offset"
        ),
        params,
    ).fetchall()

    return {
        "total":  total,
        "limit":  limit,
        "offset": offset,
        "items":  [dict(r._mapping) for r in rows],
    }


@router.post("/")
def create_page(
    body: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    slug = (body.get("slug") or "").strip()
    name = (body.get("name") or "").strip()
    if not slug or not name:
        raise HTTPException(400, "Slug und Name sind Pflichtfelder")
    if not slug.startswith("/"):
        slug = "/" + slug

    existing = db.execute(
        text("SELECT id FROM public_pages WHERE slug = :slug"),
        {"slug": slug},
    ).fetchone()
    if existing:
        raise HTTPException(409, f"Seite mit Pfad '{slug}' existiert bereits")

    result = db.execute(text("""
        INSERT INTO public_pages
          (slug, name, page_type, status, description)
        VALUES (:slug, :name, :type, 'draft', :desc)
        RETURNING id
    """), {
        "slug": slug,
        "name": name,
        "type": body.get("page_type") or "custom",
        "desc": body.get("description") or "",
    })
    new_id = result.fetchone()[0]
    db.commit()
    return {"id": new_id, "slug": slug}


@router.get("/{page_id}")
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(
        text("SELECT * FROM public_pages WHERE id = :id"),
        {"id": page_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Seite nicht gefunden")
    return dict(row._mapping)


@router.put("/{page_id}")
def save_page(
    page_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Speichert GrapesJS-Daten, HTML, CSS, Status und Meta-Infos.
    Alle Felder optional — nur übergebene werden aktualisiert."""
    updates = []
    params = {"id": page_id}

    if "grapesjs_data" in body:
        updates.append("grapesjs_data = :gjs")
        params["gjs"] = json.dumps(body.get("grapesjs_data") or {})
    if "html_content" in body:
        updates.append("html_content = :html")
        params["html"] = body.get("html_content") or ""
    if "css_content" in body:
        updates.append("css_content = :css")
        params["css"] = body.get("css_content") or ""
    if "status" in body:
        updates.append("status = :status")
        params["status"] = body.get("status") or "draft"
        if body.get("status") == "live":
            updates.append("published_at = COALESCE(published_at, NOW())")
    if "meta_title" in body:
        updates.append("meta_title = :title")
        params["title"] = body.get("meta_title") or ""
    if "meta_description" in body:
        updates.append("meta_description = :desc")
        params["desc"] = body.get("meta_description") or ""

    if not updates:
        return {"success": True, "changed": 0}

    updates.append("updated_at = NOW()")
    sql = f"UPDATE public_pages SET {', '.join(updates)} WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    return {"success": True, "changed": len(updates) - 1}


@router.delete("/{page_id}")
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(
        text("SELECT react_component FROM public_pages WHERE id=:id"),
        {"id": page_id},
    ).fetchone()
    if row and row.react_component:
        raise HTTPException(400, "System-Seiten können nicht gelöscht werden")
    db.execute(text("DELETE FROM public_pages WHERE id=:id"), {"id": page_id})
    db.commit()
    return {"success": True}


@router.patch("/{page_id}/link-product")
def link_product(
    page_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db.execute(
        text("UPDATE public_pages SET product_id=:pid, updated_at=NOW() WHERE id=:id"),
        {"pid": body.get("product_id"), "id": page_id},
    )
    db.commit()
    return {"success": True}
