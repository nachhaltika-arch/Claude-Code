"""
Admin settings & role management API routes.
"""
import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SystemSettings, RolePermission, get_db
from routers.auth_router import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin-settings"])

DEFAULT_PERMISSIONS = {
    "admin": [
        "view_dashboard", "view_leads", "create_leads", "edit_leads", "delete_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects", "manage_projects",
        "view_users", "manage_users", "view_settings", "manage_settings", "view_billing", "manage_billing",
    ],
    "auditor": [
        "view_dashboard", "view_leads", "create_leads", "edit_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects",
    ],
    "nutzer": [
        "view_dashboard", "view_audits", "download_pdf",
    ],
    "kunde": [
        "view_dashboard", "view_audits", "download_pdf",
    ],
}


# ═══════════════════════════════════════════════════════════
# System Settings
# ═══════════════════════════════════════════════════════════

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]


@router.get("/settings")
def get_settings(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(SystemSettings).all()
    return {r.key: r.value for r in rows}


@router.patch("/settings")
def update_settings(req: SettingsUpdate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    for key, value in req.settings.items():
        existing = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if existing:
            existing.value = value
            existing.updated_by = admin.id
        else:
            db.add(SystemSettings(key=key, value=value, updated_by=admin.id))
    db.commit()
    return {"message": "Einstellungen gespeichert"}


@router.post("/settings/test-email")
def test_email(admin=Depends(require_admin)):
    # Placeholder — actual email sending would go here
    return {"message": "Test-E-Mail wird gesendet (nicht implementiert)"}


# ═══════════════════════════════════════════════════════════
# Role Permissions
# ═══════════════════════════════════════════════════════════

class RolePermissionsUpdate(BaseModel):
    permissions: Dict[str, bool]


@router.get("/roles")
def get_roles(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(RolePermission).all()
    if not rows:
        _seed_permissions(db)
        rows = db.query(RolePermission).all()

    result = {}
    for r in rows:
        if r.role not in result:
            result[r.role] = {}
        result[r.role][r.permission] = r.is_allowed
    return result


@router.patch("/roles/{role}")
def update_role_permissions(role: str, req: RolePermissionsUpdate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    if role in ("admin", "superadmin"):
        raise HTTPException(400, "Admin-Rolle kann nicht geaendert werden")
    if role not in ("auditor", "nutzer", "kunde"):
        raise HTTPException(400, "Unbekannte Rolle")

    for perm, allowed in req.permissions.items():
        existing = db.query(RolePermission).filter(
            RolePermission.role == role, RolePermission.permission == perm
        ).first()
        if existing:
            existing.is_allowed = allowed
        else:
            db.add(RolePermission(role=role, permission=perm, is_allowed=allowed))
    db.commit()
    return {"message": f"Berechtigungen fuer {role} gespeichert"}


def _seed_permissions(db: Session):
    """Insert default permissions if table is empty."""
    all_perms = [
        "view_dashboard", "view_leads", "create_leads", "edit_leads", "delete_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects", "manage_projects",
        "view_users", "manage_users", "view_settings", "manage_settings", "view_billing", "manage_billing",
    ]
    for role, allowed_perms in DEFAULT_PERMISSIONS.items():
        for perm in all_perms:
            db.add(RolePermission(role=role, permission=perm, is_allowed=perm in allowed_perms))
    db.commit()
    logger.info("Default role permissions seeded")
