"""
Admin settings & role management API routes.
"""
import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SystemSettings, RolePermission, get_db
from routers.auth_router import require_admin, verlangt_recht

logger = logging.getLogger(__name__)

from services.rechte import DURCHGESETZTE_RECHTE
from services.rollen import BEARBEITBAR

router = APIRouter(prefix="/api/admin", tags=["admin-settings"])

DEFAULT_PERMISSIONS = {
    "superadmin": [
        "view_dashboard", "view_leads", "create_leads", "edit_leads", "delete_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects", "manage_projects",
        "view_users", "manage_users", "view_settings", "manage_settings", "view_billing", "manage_billing",
        "deploy_kas_pages",        # KAS-Seiten live stellen
        "manage_system_settings",  # systemkritische Einstellungen
    ],
    "admin": [
        "view_dashboard", "view_leads", "create_leads", "edit_leads", "delete_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects", "manage_projects",
        "view_users", "manage_users", "view_settings", "manage_settings", "view_billing", "manage_billing",
        # **Kein `deploy_kas_pages`** — und die Begruendung ist am 22.08.2026
        # praezisiert worden. KAS heisst **KOMPAGNON Agentur Seiten**: die
        # eigene Marketingseite, nicht die Kundenseiten. Sie live zu stellen
        # ist kein Tagesgeschaeft im Website-Bau, sondern eine Veroeffentlichung
        # im eigenen Namen — `POST /api/kas/deploy` traegt seit jeher
        # `require_superadmin`, und das bleibt so.
        #
        # Kein `manage_system_settings`: Wer Rechte vergeben darf, kann sich
        # alles geben. Diese Trennung bleibt.
    ],
    # Mitarbeiter KOMPAGNON. Bis zum 27.08.2026 hiess diese Zeile `auditor`;
    # daneben stand ein `nutzer` mit drei Rechten, der an keinen Betrieb kam.
    # Beide sind jetzt eine Rolle (Entscheidung David, siehe
    # `services/rollen.py`), und sie fuehrt **die Rechte des Auditors** —
    # das sind die, mit denen im Werkzeug tatsaechlich gearbeitet wurde.
    # Die Zusammenlegung ist damit additiv: Sie nimmt niemandem etwas weg.
    "mitarbeiter": [
        "view_dashboard", "view_leads", "create_leads", "edit_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects",
        # `manage_projects` am 22.08.2026 dazugenommen (L-05, Davids
        # Entscheidung). Die 61 Routen unter `/api/projects` stehen seit jeher
        # auf `require_innendienst` — der Innendienst arbeitet dort. Die
        # Vorgabe war irgendwann geschrieben, die Routen sind gewachsen; wo
        # beide auseinandergehen, ist nicht automatisch die Route falsch. Erst
        # dadurch laesst sich das Recht durchsetzen, ohne jemandem etwas
        # wegzunehmen.
        "manage_projects",
    ],
    "kunde": [
        "view_dashboard", "view_audits", "download_pdf",
    ],
}

PERM_LABELS = {
    "view_dashboard":         "Dashboard ansehen",
    "view_leads":             "Leads ansehen",
    "create_leads":           "Leads anlegen",
    "edit_leads":             "Leads bearbeiten",
    "delete_leads":           "Leads loeschen",
    "view_audits":            "Audits ansehen",
    "create_audits":          "Audits erstellen",
    "download_pdf":           "PDFs herunterladen",
    "view_projects":          "Projekte ansehen",
    "manage_projects":        "Projekte verwalten",
    "view_users":             "Benutzer ansehen",
    "manage_users":           "Benutzer verwalten",
    "view_settings":          "Einstellungen ansehen",
    "manage_settings":        "Einstellungen verwalten",
    "view_billing":           "Abrechnung ansehen",
    "manage_billing":         "Abrechnung verwalten",
    "deploy_kas_pages":       "KAS-Seiten live deployen",
    "manage_system_settings": "Systemkritische Einstellungen aendern",
}


# ═══════════════════════════════════════════════════════════
# System Settings
# ═══════════════════════════════════════════════════════════

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]


@router.get("/settings", dependencies=[Depends(verlangt_recht("view_settings"))])
def get_settings(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(SystemSettings).all()
    return {r.key: r.value for r in rows}


@router.patch("/settings", dependencies=[Depends(verlangt_recht("manage_settings"))])
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


# ── `POST /settings/test-email` entfernt am 2026-08-31 (L-105) ────────
#
# Er hat **nichts getan und das Gegenteil geantwortet**: „Test-E-Mail wird
# gesendet (nicht implementiert)". Wer den ersten Halbsatz liest und den
# zweiten ueberliest — und in einer Antwort liest man den ersten —, haelt den
# Versand fuer angestossen.
#
# Gerufen hat ihn niemand: `tools/unaufgerufene-routen.py` fuehrte ihn am
# 31.08.2026 unter den 100 Endpunkten ohne Aufrufer. Der **arbeitende** Weg
# ist `POST /api/automations/test-email?recipient=…`; ihn ruft die
# Einstellungsseite, und er verschickt wirklich.
#
# Zwei Wege zur selben Sache, von denen einer nur so tut, sind schlimmer als
# einer: Wer den falschen findet, sucht den Fehler danach beim Mailversand.
# `tests/test_testmail_einer.py` haelt fest, dass es bei einem bleibt.


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

    rollen = {}
    for r in rows:
        rollen.setdefault(r.role, {})[r.permission] = r.is_allowed

    # Bis zum 18.08.2026 wurde diese Tabelle **nirgends** zur Rechtevergabe
    # gelesen (L-05): Ein Haken liess sich setzen und wegnehmen, ohne dass
    # etwas geschah. Jetzt haengt an einem Teil davon wirklich eine Sperre —
    # und der Bildschirm muss beides auseinanderhalten koennen. Was hier nicht
    # steht, ist Beschreibung, keine Zusicherung.
    return {
        **rollen,
        "rollen": rollen,
        "durchgesetzt": sorted(DURCHGESETZTE_RECHTE),
    }


# Wer Rechte vergeben darf, kann sich alles geben. Diese eine Trennung
# bleibt beim Superadmin (L-05, Entscheidung 22.08.2026) — der Admin
# verliert die Rechtepflege, und das ist der Sinn.
@router.patch("/roles/{role}",
              dependencies=[Depends(verlangt_recht("manage_system_settings"))])
def update_role_permissions(role: str, req: RolePermissionsUpdate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    if role == "superadmin":
        raise HTTPException(400, "Superadmin-Rolle kann nicht ueber die UI geaendert werden")
    if role == "admin":
        raise HTTPException(400, "Admin-Rolle kann nicht geaendert werden")
    if role not in BEARBEITBAR:
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
        "deploy_kas_pages", "manage_system_settings",
    ]
    for role, allowed_perms in DEFAULT_PERMISSIONS.items():
        for perm in all_perms:
            db.add(RolePermission(role=role, permission=perm, is_allowed=perm in allowed_perms))
    db.commit()
    logger.info("Default role permissions seeded")
