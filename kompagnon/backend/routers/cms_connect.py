"""
CMS Connection endpoints for customer profiles.
PUT  /api/customers/{id}/cms-connection  — save credentials
GET  /api/customers/{id}/cms-connection  — load (no password)
POST /api/customers/{id}/cms-test        — test live connection
POST /api/customers/{id}/publish         — push HTML to CMS
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db, Customer
from routers.auth_router import require_any_auth

router = APIRouter(prefix="/api/customers", tags=["cms"])


# ── Pydantic schemas ──────────────────────────────────────────────

class CmsConnectionIn(BaseModel):
    cms_type: str                    # "wordpress_elementor" | "webflow" | "none"
    cms_url: Optional[str] = ""
    cms_username: Optional[str] = "" # WP username OR Webflow site_id
    cms_password: Optional[str] = "" # WP app-password OR Webflow API token; "" = keep existing


class PublishIn(BaseModel):
    html: str
    css: Optional[str] = ""
    page_title: str


# ── Helpers ───────────────────────────────────────────────────────

def _get_customer_or_404(customer_id: int, db: Session) -> Customer:
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return c


def _decrypt(encrypted: str) -> str:
    from utils.encryption import decrypt_password
    return decrypt_password(encrypted)


# ── Routes ────────────────────────────────────────────────────────

@router.put("/{customer_id}/cms-connection")
def save_cms_connection(
    customer_id: int,
    data: CmsConnectionIn,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    customer = _get_customer_or_404(customer_id, db)
    from utils.encryption import encrypt_password

    customer.cms_type = data.cms_type
    customer.cms_url = (data.cms_url or "").rstrip("/")
    customer.cms_username = data.cms_username or ""
    if data.cms_password:  # only overwrite if a new password was provided
        customer.cms_password_encrypted = encrypt_password(data.cms_password)

    db.commit()
    return {"ok": True}


@router.get("/{customer_id}/cms-connection")
def get_cms_connection(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    customer = _get_customer_or_404(customer_id, db)
    return {
        "cms_type": customer.cms_type or "",
        "cms_url": customer.cms_url or "",
        "cms_username": customer.cms_username or "",
        "has_cms_connection": bool(customer.cms_type and customer.cms_type != "none" and customer.cms_password_encrypted),
    }


@router.post("/{customer_id}/cms-test")
async def test_cms_connection(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    customer = _get_customer_or_404(customer_id, db)

    if not customer.cms_password_encrypted:
        raise HTTPException(status_code=400, detail="Keine CMS-Verbindung konfiguriert")

    password = _decrypt(customer.cms_password_encrypted)

    if customer.cms_type == "wordpress_elementor":
        from services.wordpress_service import test_wp_connection
        ok, msg = await test_wp_connection(customer.cms_url, customer.cms_username, password)
    elif customer.cms_type == "webflow":
        from services.webflow_service import test_webflow_connection
        ok, msg = await test_webflow_connection(password)  # password = API token
    else:
        return {"ok": False, "message": f"Unbekannter CMS-Typ: {customer.cms_type}"}

    return {
        "ok": ok,
        "message": msg if msg else ("Verbindung erfolgreich ✓" if ok else "Verbindung fehlgeschlagen"),
    }


@router.post("/{customer_id}/publish")
async def publish_to_cms(
    customer_id: int,
    data: PublishIn,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    customer = _get_customer_or_404(customer_id, db)

    if not customer.cms_password_encrypted:
        raise HTTPException(status_code=400, detail="Keine CMS-Verbindung konfiguriert")

    password = _decrypt(customer.cms_password_encrypted)

    if customer.cms_type == "wordpress_elementor":
        from services.wordpress_service import push_to_wordpress
        ok, result = await push_to_wordpress(
            customer.cms_url, customer.cms_username, password,
            data.html, data.css or "", data.page_title,
        )
    elif customer.cms_type == "webflow":
        from services.webflow_service import push_to_webflow
        # cms_username holds the Site ID for Webflow
        ok, result = await push_to_webflow(
            password, customer.cms_username,
            data.html, data.css or "", data.page_title,
        )
    else:
        return {"success": False, "page_url": "", "message": f"Unbekannter CMS-Typ: {customer.cms_type}"}

    return {
        "success": ok,
        "page_url": result if ok else "",
        "message": "Seite als Entwurf erstellt ✓" if ok else result,
    }
