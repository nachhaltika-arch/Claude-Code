"""
Website Templates API
POST /api/templates/upload  - Upload a ZIP containing HTML/CSS template (admin only)
GET  /api/templates/        - List all active templates
GET  /api/templates/{id}    - Get single template
"""
import io
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import require_admin

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("allgemein"),
    tags: str = Form(""),
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Upload a ZIP archive containing an HTML/CSS template."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Nur ZIP-Dateien erlaubt")

    raw = await file.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Ungültige ZIP-Datei")

    names = zf.namelist()

    # Find HTML file — prefer index.html, otherwise first .html
    html_name = next((n for n in names if n.lower().endswith("index.html")), None)
    if not html_name:
        html_name = next((n for n in names if n.lower().endswith(".html")), None)

    # Find CSS file — prefer style.css, otherwise first .css
    css_name = next((n for n in names if n.lower().endswith("style.css")), None)
    if not css_name:
        css_name = next((n for n in names if n.lower().endswith(".css")), None)

    html_content = zf.read(html_name).decode("utf-8", errors="replace") if html_name else None
    css_content = zf.read(css_name).decode("utf-8", errors="replace") if css_name else None

    if not html_content:
        raise HTTPException(status_code=400, detail="Keine HTML-Datei im ZIP gefunden")

    row = db.execute(
        text("""
            INSERT INTO website_templates
              (name, description, source, html_content, css_content, tags, category, created_at, updated_at)
            VALUES
              (:name, :desc, 'upload', :html, :css, :tags, :cat, NOW(), NOW())
            RETURNING id, name, created_at
        """),
        {
            "name": name,
            "desc": description,
            "html": html_content,
            "css": css_content,
            "tags": tags,
            "cat": category,
        },
    ).fetchone()
    db.commit()

    return {"id": row.id, "name": row.name, "created_at": row.created_at.isoformat()}


@router.get("/")
def list_templates(db: Session = Depends(get_db)):
    """List all active templates (without full HTML/CSS content)."""
    rows = db.execute(
        text("""
            SELECT id, name, description, source, source_url, thumbnail_url,
                   tags, category, is_active, created_at
            FROM website_templates
            WHERE is_active = true
            ORDER BY created_at DESC
        """)
    ).fetchall()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "source": r.source,
            "source_url": r.source_url,
            "thumbnail_url": r.thumbnail_url,
            "tags": r.tags,
            "category": r.category,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a single template including HTML/CSS content."""
    row = db.execute(
        text("SELECT * FROM website_templates WHERE id = :id"),
        {"id": template_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")
    return dict(row._mapping)
