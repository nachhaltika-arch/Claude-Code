"""
File upload/download API for project files.
Stores files in /uploads/{lead_id}/ and metadata in project_files table.
"""
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from routers.auth_router import get_current_user, require_admin

logger = logging.getLogger(__name__)


def _get_lead_by_portal_token(portal_token: str, db: Session):
    """Resolve portal token to lead, raise 404 if invalid."""
    row = db.execute(
        text("SELECT id FROM leads WHERE customer_token = :t"),
        {"t": portal_token},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ungültiger Zugangslink")
    return row[0]  # lead_id

router = APIRouter(prefix="/api/files", tags=["files"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "pdf",
    "doc", "docx", "txt", "zip", "svg", "ai", "eps",
}

UPLOADS_BASE = Path("uploads")


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _lead_dir(lead_id: int) -> Path:
    d = UPLOADS_BASE / str(lead_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── POST /api/files/upload/{lead_id} ──────────────────────────

@router.post("/upload/{lead_id}")
async def upload_file(
    lead_id: int,
    file: UploadFile = File(...),
    file_type: str = Form(default="sonstiges"),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate extension
    ext = _ext(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Dateityp .{ext} nicht erlaubt. Erlaubt: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate file_type enum
    valid_types = {"logo", "foto", "text", "zugangsdaten", "sonstiges"}
    if file_type not in valid_types:
        file_type = "sonstiges"

    # Read content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Datei zu groß. Maximum: 20 MB")

    # Save to disk
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest = _lead_dir(lead_id) / unique_name
    dest.write_bytes(content)

    # Determine uploader role
    uploaded_by_role = "admin" if getattr(current_user, "role", "") in ("admin", "auditor") else "kunde"

    # Insert DB record
    db.execute(text("""
        INSERT INTO project_files
            (lead_id, uploaded_by_role, filename, original_filename,
             file_type, file_size, file_path, note, uploaded_at)
        VALUES
            (:lead_id, :uploaded_by_role, :filename, :original_filename,
             :file_type, :file_size, :file_path, :note, :uploaded_at)
    """), {
        "lead_id": lead_id,
        "uploaded_by_role": uploaded_by_role,
        "filename": unique_name,
        "original_filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "file_path": str(dest),
        "note": note,
        "uploaded_at": datetime.utcnow(),
    })
    db.commit()

    row = db.execute(text(
        "SELECT id FROM project_files WHERE filename = :fn ORDER BY id DESC LIMIT 1"
    ), {"fn": unique_name}).fetchone()

    logger.info(f"✓ Datei hochgeladen: {file.filename} für Lead {lead_id} (user {current_user.id})")

    return {
        "id": row[0] if row else None,
        "filename": unique_name,
        "original_filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "uploaded_by_role": uploaded_by_role,
        "note": note,
    }


# ── GET /api/files/{lead_id} ───────────────────────────────────

@router.get("/{lead_id}")
def list_files(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = db.execute(text("""
        SELECT id, lead_id, uploaded_by_role, filename, original_filename,
               file_type, file_size, file_path, uploaded_at, note
        FROM project_files
        WHERE lead_id = :lead_id
        ORDER BY uploaded_at DESC
    """), {"lead_id": lead_id}).fetchall()

    return [
        {
            "id": r[0],
            "lead_id": r[1],
            "uploaded_by_role": r[2],
            "filename": r[3],
            "original_filename": r[4],
            "file_type": r[5],
            "file_size": r[6],
            "file_path": r[7],
            "uploaded_at": r[8].isoformat() if r[8] else None,
            "note": r[9],
        }
        for r in rows
    ]


# ── GET /api/files/download/{file_id} ─────────────────────────

@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(text("""
        SELECT file_path, original_filename, file_type
        FROM project_files WHERE id = :id
    """), {"id": file_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    file_path, original_filename, file_type = row

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Datei nicht mehr auf dem Server vorhanden")

    # Determine media type for inline preview (images/pdf) vs attachment
    ext = _ext(original_filename or "")
    inline_types = {"jpg", "jpeg", "png", "gif", "pdf", "svg"}
    disposition = "inline" if ext in inline_types else "attachment"

    return FileResponse(
        path=file_path,
        filename=original_filename,
        content_disposition_type=disposition,
    )


# ── DELETE /api/files/{file_id} ───────────────────────────────

@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    row = db.execute(text("""
        SELECT file_path, original_filename FROM project_files WHERE id = :id
    """), {"id": file_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    file_path, original_filename = row

    # Delete from disk
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Datei konnte nicht gelöscht werden: {file_path}: {e}")

    # Delete DB record
    db.execute(text("DELETE FROM project_files WHERE id = :id"), {"id": file_id})
    db.commit()

    logger.info(f"✓ Datei gelöscht: {original_filename} (id={file_id}, admin={current_user.id})")

    return {"deleted": True, "id": file_id}


# ── Portal endpoints (no JWT — authenticated via portal token) ─

@router.post("/portal/{portal_token}/upload")
async def portal_upload_file(
    portal_token: str,
    file: UploadFile = File(...),
    file_type: str = Form(default="sonstiges"),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
):
    lead_id = _get_lead_by_portal_token(portal_token, db)

    ext = _ext(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Dateityp .{ext} nicht erlaubt. Erlaubt: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    valid_types = {"logo", "foto", "text", "zugangsdaten", "sonstiges"}
    if file_type not in valid_types:
        file_type = "sonstiges"

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Datei zu groß. Maximum: 20 MB")

    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest = _lead_dir(lead_id) / unique_name
    dest.write_bytes(content)

    db.execute(text("""
        INSERT INTO project_files
            (lead_id, uploaded_by_role, filename, original_filename,
             file_type, file_size, file_path, note, uploaded_at)
        VALUES
            (:lead_id, 'kunde', :filename, :original_filename,
             :file_type, :file_size, :file_path, :note, :uploaded_at)
    """), {
        "lead_id": lead_id,
        "filename": unique_name,
        "original_filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "file_path": str(dest),
        "note": note,
        "uploaded_at": datetime.utcnow(),
    })
    db.commit()

    row = db.execute(text(
        "SELECT id FROM project_files WHERE filename = :fn ORDER BY id DESC LIMIT 1"
    ), {"fn": unique_name}).fetchone()

    logger.info(f"✓ Portal-Datei hochgeladen: {file.filename} für Lead {lead_id}")

    return {
        "id": row[0] if row else None,
        "filename": unique_name,
        "original_filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "uploaded_by_role": "kunde",
        "note": note,
    }


@router.get("/portal/{portal_token}")
def portal_list_files(
    portal_token: str,
    db: Session = Depends(get_db),
):
    lead_id = _get_lead_by_portal_token(portal_token, db)

    rows = db.execute(text("""
        SELECT id, lead_id, uploaded_by_role, filename, original_filename,
               file_type, file_size, file_path, uploaded_at, note
        FROM project_files
        WHERE lead_id = :lead_id
        ORDER BY uploaded_at DESC
    """), {"lead_id": lead_id}).fetchall()

    return [
        {
            "id": r[0],
            "lead_id": r[1],
            "uploaded_by_role": r[2],
            "filename": r[3],
            "original_filename": r[4],
            "file_type": r[5],
            "file_size": r[6],
            "file_path": r[7],
            "uploaded_at": r[8].isoformat() if r[8] else None,
            "note": r[9],
        }
        for r in rows
    ]


@router.get("/portal/{portal_token}/download/{file_id}")
def portal_download_file(
    portal_token: str,
    file_id: int,
    db: Session = Depends(get_db),
):
    lead_id = _get_lead_by_portal_token(portal_token, db)

    row = db.execute(text("""
        SELECT file_path, original_filename, lead_id
        FROM project_files WHERE id = :id
    """), {"id": file_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    file_path, original_filename, file_lead_id = row

    if file_lead_id != lead_id:
        raise HTTPException(status_code=403, detail="Zugriff verweigert")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Datei nicht mehr auf dem Server vorhanden")

    ext = _ext(original_filename or "")
    inline_types = {"jpg", "jpeg", "png", "gif", "pdf", "svg"}
    disposition = "inline" if ext in inline_types else "attachment"

    return FileResponse(
        path=file_path,
        filename=original_filename,
        content_disposition_type=disposition,
    )
