"""
Kundenportal endpoints — only for JWT-authenticated users with role 'kunde'.

GET  /api/portal/me                — project + phase progress
GET  /api/portal/messages          — message thread
POST /api/portal/messages          — send a message
GET  /api/portal/documents         — list uploaded files
POST /api/portal/documents/upload  — upload a file (multipart)
"""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db, Project, ProjectChecklist, Lead
from routers.auth_router import get_current_user

router = APIRouter(prefix="/api/portal", tags=["portal"])

# ── Phase metadata ────────────────────────────────────────────────

PHASE_META = [
    (1, "Kickoff & Strategie",    "Ziele, Zielgruppe und Sitemap definiert"),
    (2, "Texterstellung",          "Alle Seiteninhalte verfasst und freigegeben"),
    (3, "Design & Design",         "Startseite & Unterseiten im Design-Tool"),
    (4, "Entwicklung",             "Technische Umsetzung im CMS"),
    (5, "SEO & GEO-Optimierung",  "Meta-Tags, Ladezeit, lokale Sichtbarkeit"),
    (6, "Review & Freigabe",       "Gemeinsame Abnahme aller Seiten"),
    (7, "Go-live & Übergabe",      "Domain live schalten, Einweisung, Support"),
]

STATUS_LABEL = {
    "phase_1": "Kickoff läuft",    "phase_2": "Texterstellung",
    "phase_3": "Design & Design",  "phase_4": "In Entwicklung",
    "phase_5": "SEO & Optimierung","phase_6": "Review",
    "phase_7": "Go-live",          "completed": "Abgeschlossen",
}


def _phase_number(status: str) -> int:
    for i in range(1, 8):
        if status == f"phase_{i}":
            return i
    return 7 if status == "completed" else 1


def _customer_id(user) -> int:
    """Stable identifier for a customer's portal data."""
    return user.lead_id if user.lead_id else user.id


# ── GET /api/portal/me ────────────────────────────────────────────

@router.get("/me")
def get_portal_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cid = _customer_id(user)

    # Resolve lead
    lead = db.query(Lead).filter(Lead.id == cid).first() if user.lead_id else None
    project_name = (lead.company_name if lead else None) or "Mein Projekt"

    # Try to find a project
    project = None
    if user.lead_id:
        project = (
            db.query(Project)
            .filter(Project.lead_id == user.lead_id)
            .order_by(Project.created_at.desc())
            .first()
        )

    if not project:
        return {
            "project_name": project_name,
            "project_status": "In Vorbereitung",
            "current_phase": 1,
            "phases": [
                {
                    "number": n, "label": lbl, "description": desc,
                    "done": 0, "total": 0,
                    "state": "active" if n == 1 else "locked",
                }
                for n, lbl, desc in PHASE_META
            ],
        }

    current = _phase_number(project.status)

    # Aggregate checklist progress per phase
    items = db.query(ProjectChecklist).filter(ProjectChecklist.project_id == project.id).all()
    counts = {i: {"done": 0, "total": 0} for i in range(1, 8)}
    for it in items:
        if 1 <= it.phase <= 7:
            counts[it.phase]["total"] += 1
            if it.is_completed:
                counts[it.phase]["done"] += 1

    phases = [
        {
            "number": n, "label": lbl, "description": desc,
            "done": counts[n]["done"], "total": counts[n]["total"],
            "state": "done" if n < current else ("active" if n == current else "locked"),
        }
        for n, lbl, desc in PHASE_META
    ]

    # Netlify / DNS-Guide Daten für den Kunden (optional)
    netlify_info = None
    try:
        from services.netlify_service import generate_dns_guide
        netlify_domain = getattr(project, "netlify_domain", None)
        netlify_status = getattr(project, "netlify_domain_status", None)
        netlify_site_url = getattr(project, "netlify_site_url", None)
        if netlify_domain:
            netlify_info = {
                "domain":     netlify_domain,
                "status":     netlify_status or "pending",
                "site_url":   netlify_site_url,
                "ssl_active": bool(getattr(project, "netlify_ssl_active", False)),
                "guide":      generate_dns_guide(netlify_domain, netlify_site_url or ""),
            }
    except Exception:
        pass

    return {
        "project_id": project.id,
        "project_name": project_name,
        "project_status": STATUS_LABEL.get(project.status, "In Bearbeitung"),
        "current_phase": current,
        "phases": phases,
        "netlify": netlify_info,
    }


# ── Messages ──────────────────────────────────────────────────────

class MessageIn(BaseModel):
    text: str


@router.get("/messages")
def get_messages(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cid = _customer_id(user)
    rows = db.execute(
        text("SELECT id, sender_role, text, created_at FROM portal_messages "
             "WHERE customer_id = :cid ORDER BY created_at ASC"),
        {"cid": cid},
    ).fetchall()
    return [
        {"id": r[0], "sender_role": r[1], "text": r[2], "created_at": str(r[3])}
        for r in rows
    ]


@router.post("/messages", status_code=201)
def post_message(data: MessageIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not data.text.strip():
        raise HTTPException(400, "Nachricht darf nicht leer sein")
    cid = _customer_id(user)
    db.execute(
        text("INSERT INTO portal_messages (customer_id, sender_role, text, created_at) "
             "VALUES (:cid, :role, :text, :now)"),
        {"cid": cid, "role": user.role, "text": data.text.strip(), "now": datetime.utcnow()},
    )
    db.commit()
    return {"ok": True}


# ── Documents ─────────────────────────────────────────────────────

@router.get("/documents")
def get_documents(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cid = _customer_id(user)
    rows = db.execute(
        text("SELECT id, filename, filepath, created_at FROM portal_documents "
             "WHERE customer_id = :cid ORDER BY created_at DESC"),
        {"cid": cid},
    ).fetchall()
    return [
        {"id": r[0], "filename": r[1], "filepath": r[2], "created_at": str(r[3])}
        for r in rows
    ]


@router.post("/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cid = _customer_id(user)
    upload_dir = f"/uploads/portal/{cid}"
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = os.path.basename(file.filename or "upload")
    dest = os.path.join(upload_dir, safe_name)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    db.execute(
        text("INSERT INTO portal_documents (customer_id, filename, filepath, created_at) "
             "VALUES (:cid, :fn, :fp, :now)"),
        {"cid": cid, "fn": safe_name, "fp": dest, "now": datetime.utcnow()},
    )
    db.commit()
    return {"ok": True, "filename": safe_name}
