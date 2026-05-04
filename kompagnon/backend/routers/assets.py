"""
Asset-Router für GrapesJS Studio SDK Asset Manager.
Führt Kunden-/Admin-Uploads (project_files) + Crawler-Bilder
(website_content_cache.images) in einer einheitlichen Liste zusammen.
"""
import json
import logging
import os
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assets", tags=["assets"])

_UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "uploads"))
_ALLOWED_IMG_EXT = {"jpg", "jpeg", "png", "gif", "svg", "webp"}
_MAX_SIZE = 20 * 1024 * 1024  # 20 MB


def _lead_dir(lead_id: int) -> Path:
    d = _UPLOAD_ROOT / f"lead_{lead_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.get("/project/{project_id}")
def get_project_assets(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Liefert alle verfügbaren Bilder für einen Projekt-Kontext.
    Zusammenführung aus:
      1. project_files (Kunden-Uploads + Admin-Uploads)
      2. website_content_cache.images (Crawler-Bilder, JSON-Array)
    """
    assets = []

    # Lead-ID über Projekt ermitteln
    project = db.execute(
        text("SELECT lead_id FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead_id = project.lead_id

    # ── 1. Dateien aus project_files ────────────────────────
    if lead_id:
        try:
            files = db.execute(text("""
                SELECT id, original_filename, file_type, file_size, uploaded_at
                FROM project_files
                WHERE lead_id = :lid
                  AND (
                    file_type IN ('logo','foto','sonstiges')
                    OR original_filename ~* '\\.(jpg|jpeg|png|gif|svg|webp)$'
                  )
                ORDER BY uploaded_at DESC
            """), {"lid": lead_id}).fetchall()

            for f in files:
                ext = (f.original_filename or "").split(".")[-1].lower()
                if ext not in _ALLOWED_IMG_EXT:
                    continue
                assets.append({
                    "type":     "image",
                    "src":      f"/api/files/download/{f.id}",
                    "name":     f.original_filename or f"Datei {f.id}",
                    "category": f.file_type or "upload",
                    "source":   "portal_upload",
                })
        except Exception as e:
            logger.warning(f"assets: project_files query failed: {e}")

    # ── 2. Crawler-Bilder aus website_content_cache.images (JSON) ──
    # customer_id in website_content_cache entspricht lead_id
    # (siehe crawler.scrape_content).
    if lead_id:
        try:
            rows = db.execute(text("""
                SELECT images, url, title
                FROM website_content_cache
                WHERE customer_id = :lid
                  AND images IS NOT NULL
                ORDER BY scraped_at DESC
                LIMIT 25
            """), {"lid": lead_id}).fetchall()

            seen = set()
            for r in rows:
                try:
                    arr = json.loads(r.images) if isinstance(r.images, str) else (r.images or [])
                except Exception:
                    arr = []
                for img_url in arr:
                    if not isinstance(img_url, str) or not img_url:
                        continue
                    if img_url in seen:
                        continue
                    low = img_url.lower().split("?")[0]
                    if not any(low.endswith("." + e) for e in _ALLOWED_IMG_EXT):
                        continue
                    seen.add(img_url)
                    assets.append({
                        "type":     "image",
                        "src":      img_url,
                        "name":     img_url.split("/")[-1] or "Crawler-Bild",
                        "category": "alte_website",
                        "source":   "crawler",
                    })
                    if len(seen) >= 60:
                        break
                if len(seen) >= 60:
                    break
        except Exception as e:
            logger.warning(f"assets: crawler images query failed: {e}")

    return {"assets": assets, "total": len(assets)}


@router.post("/project/{project_id}/upload")
async def upload_asset(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Bild direkt aus GrapesJS Asset Manager hochladen.
    Speichert in project_files (auf Disk wie files.py) und gibt
    das Studio-SDK-Upload-Response-Format zurück.
    """
    project = db.execute(
        text("SELECT lead_id FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not project or not project.lead_id:
        raise HTTPException(404, "Projekt / Lead nicht gefunden")
    lead_id = project.lead_id

    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in _ALLOWED_IMG_EXT:
        raise HTTPException(400, f"Dateityp .{ext} nicht erlaubt")

    content = await file.read()
    if len(content) > _MAX_SIZE:
        raise HTTPException(413, "Datei zu groß (max 20 MB)")

    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest = _lead_dir(lead_id) / unique_name
    dest.write_bytes(content)

    uploaded_by_role = "admin" if getattr(current_user, "role", "") in ("admin", "auditor") else "kunde"

    db.execute(text("""
        INSERT INTO project_files
            (lead_id, uploaded_by_role, filename, original_filename,
             file_type, file_size, file_path, note, uploaded_at)
        VALUES
            (:lead_id, :uploaded_by_role, :filename, :original_filename,
             'foto', :file_size, :file_path, '', :uploaded_at)
    """), {
        "lead_id": lead_id,
        "uploaded_by_role": uploaded_by_role,
        "filename": unique_name,
        "original_filename": file.filename,
        "file_size": len(content),
        "file_path": str(dest),
        "uploaded_at": datetime.utcnow(),
    })
    db.commit()

    row = db.execute(
        text("SELECT id FROM project_files WHERE filename = :fn ORDER BY id DESC LIMIT 1"),
        {"fn": unique_name},
    ).fetchone()
    file_id = row[0] if row else None

    return {
        "data": [{
            "src":  f"/api/files/download/{file_id}",
            "name": file.filename,
            "type": "image",
        }]
    }
