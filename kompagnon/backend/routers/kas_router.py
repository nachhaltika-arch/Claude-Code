"""
KAS Website Router — KOMPAGNON eigene Seiten (KAS = KOMPAGNON Agentur Seiten)

Alle Endpunkte erfordern mindestens Admin-Rechte.
Der Deploy-Endpunkt und das Anlegen der Netlify-Site erfordern Superadmin.

Endpunkte:
    GET    /api/kas/pages              — alle KAS-Seiten (Admin)
    POST   /api/kas/pages              — neue Seite anlegen (Admin)
    PUT    /api/kas/pages/{id}         — Seite bearbeiten (Admin)
    DELETE /api/kas/pages/{id}         — Seite loeschen (Admin)
    GET    /api/kas/pages/{id}/editor  — GrapesJS-Daten laden (Admin)
    POST   /api/kas/pages/{id}/editor  — GrapesJS-Daten speichern (Admin)
    GET    /api/kas/site               — Netlify-Site-Info (Admin)
    POST   /api/kas/site               — Netlify-Site anlegen (Superadmin)
    POST   /api/kas/deploy             — Alle Seiten live deployen (Superadmin)
"""
import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, KasPage, KasGjsData, SystemSettings
from routers.auth_router import require_admin, require_superadmin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kas", tags=["kas"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class KasPageCreate(BaseModel):
    titel:            str
    pfad:             str
    meta_description: Optional[str] = ""
    position:         Optional[int] = 0
    ist_startseite:   Optional[bool] = False
    notizen:          Optional[str] = ""


class KasPageUpdate(BaseModel):
    titel:            Optional[str] = None
    pfad:             Optional[str] = None
    meta_description: Optional[str] = None
    position:         Optional[int] = None
    status:           Optional[str] = None
    ist_startseite:   Optional[bool] = None
    notizen:          Optional[str] = None


class GjsDataBody(BaseModel):
    html:    str = ""
    css:     str = ""
    gjsData: dict = {}


# ── Seiten-Endpunkte ──────────────────────────────────────────────────────────

@router.get("/pages")
def list_kas_pages(db: Session = Depends(get_db), _=Depends(require_admin)):
    pages = db.query(KasPage).order_by(KasPage.position, KasPage.id).all()
    return [_serialize(p, db) for p in pages]


@router.post("/pages", status_code=201)
def create_kas_page(
    body: KasPageCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    page = KasPage(**body.model_dump())
    db.add(page)
    try:
        db.commit()
        db.refresh(page)
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Anlegen fehlgeschlagen: {str(e)[:200]}")
    return _serialize(page, db)


@router.put("/pages/{page_id}")
def update_kas_page(
    page_id: int,
    body: KasPageUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    page = db.query(KasPage).filter(KasPage.id == page_id).first()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    page.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(page)
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")
    return _serialize(page, db)


@router.delete("/pages/{page_id}", status_code=204)
def delete_kas_page(
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    page = db.query(KasPage).filter(KasPage.id == page_id).first()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")
    if page.ist_startseite:
        raise HTTPException(403, "Startseite kann nicht geloescht werden")
    db.delete(page)
    db.commit()


# ── GrapesJS Editor-Endpunkte ─────────────────────────────────────────────────

@router.get("/pages/{page_id}/editor")
def get_editor_data(
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    gjs = db.query(KasGjsData).filter(KasGjsData.page_id == page_id).first()
    if not gjs:
        return {"html": "", "css": "", "gjsData": {}}
    return {
        "html":    gjs.html or "",
        "css":     gjs.css or "",
        "gjsData": gjs.gjs_data or {},
    }


@router.post("/pages/{page_id}/editor")
def save_editor_data(
    page_id: int,
    body: GjsDataBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    # Script-Inhalte erkennen und im Audit-Log festhalten.
    has_scripts = bool(re.search(r'<script[\s>]', body.html or "", re.IGNORECASE))
    has_iframes = bool(re.search(r'<iframe[\s>]', body.html or "", re.IGNORECASE))
    has_event_handlers = bool(re.search(
        r'\bon\w+\s*=', body.html or "", re.IGNORECASE
    ))
    if has_scripts or has_iframes or has_event_handlers:
        logger.warning(
            "KAS Script-Inhalt gespeichert | "
            f"page_id={page_id} | "
            f"user={getattr(current_user, 'email', 'unknown')} | "
            f"scripts={has_scripts} | "
            f"iframes={has_iframes} | "
            f"event_handlers={has_event_handlers}"
        )

    page = db.query(KasPage).filter(KasPage.id == page_id).first()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")

    gjs = db.query(KasGjsData).filter(KasGjsData.page_id == page_id).first()
    if gjs:
        gjs.html = body.html
        gjs.css  = body.css
        gjs.gjs_data = body.gjsData
        gjs.saved_at = datetime.utcnow()
    else:
        gjs = KasGjsData(
            page_id=page_id,
            html=body.html,
            css=body.css,
            gjs_data=body.gjsData,
        )
        db.add(gjs)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")
    return {"success": True}


# ── Netlify-Site ──────────────────────────────────────────────────────────────

@router.get("/site")
def get_kas_site(db: Session = Depends(get_db), _=Depends(require_admin)):
    site_id     = _get_setting(db, "kas_netlify_site_id")
    site_url    = _get_setting(db, "kas_netlify_site_url")
    last_deploy = _get_setting(db, "kas_last_deploy")
    return {
        "site_id":     site_id,
        "site_url":    site_url,
        "configured":  bool(site_id),
        "last_deploy": last_deploy,
    }


@router.post("/site")
async def create_kas_site(
    db: Session = Depends(get_db),
    user=Depends(require_superadmin),
):
    """Legt eine neue Netlify-Site fuer KAS an (nur Superadmin)."""
    existing = _get_setting(db, "kas_netlify_site_id")
    if existing:
        raise HTTPException(409, f"KAS-Site bereits vorhanden: {existing}")

    from services.netlify_service import create_site
    try:
        result = await create_site("kompagnon-kas-website")
    except ValueError as e:
        # Token fehlt in der Env — HTTP 400 mit klarer Fehlermeldung
        logger.error(f"KAS Netlify Token fehlt: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"KAS Netlify create_site failed: {e}")
        raise HTTPException(502, f"Netlify-Site konnte nicht angelegt werden: {str(e)[:150]}")

    _set_setting(db, "kas_netlify_site_id",  result["site_id"],  user.id)
    _set_setting(db, "kas_netlify_site_url", result["site_url"], user.id)
    logger.info(f"KAS Netlify site created: {result['site_id']}")

    return {
        "site_id":  result["site_id"],
        "site_url": result["site_url"],
    }


# ── Deploy — NUR Superadmin ──────────────────────────────────────────────────

@router.post("/deploy")
async def deploy_kas_pages(
    db: Session = Depends(get_db),
    user=Depends(require_superadmin),
):
    """Deployt alle KAS-Seiten auf die eigene Netlify-Site. Nur Superadmin."""
    site_id = _get_setting(db, "kas_netlify_site_id")
    if not site_id:
        raise HTTPException(400, "Keine KAS-Netlify-Site konfiguriert. Zuerst Site anlegen.")

    pages = db.query(KasPage).order_by(KasPage.position, KasPage.id).all()
    if not pages:
        raise HTTPException(400, "Keine KAS-Seiten vorhanden.")

    # ── Seiten-Dateien zusammenstellen ────────────────────────────────────
    page_files: dict = {}
    css_parts: list = []
    for page in pages:
        gjs = db.query(KasGjsData).filter(KasGjsData.page_id == page.id).first()
        html = gjs.html if gjs and gjs.html else "<p>Seite hat noch keinen Inhalt.</p>"
        css  = gjs.css  if gjs and gjs.css  else ""
        if css:
            css_parts.append(css)

        path = (page.pfad or "/").strip("/")
        is_home = page.ist_startseite or path in ("", "index", "home", "startseite")
        filename = "index.html" if is_home else f"{path}/index.html"

        page_files[filename] = {
            "html":       html,
            "css":        css,
            "page_title": page.titel or "KOMPAGNON",
            "meta_desc":  page.meta_description or "",
        }

    shared_css = "\n".join(dict.fromkeys(css_parts))

    # DB-Verbindung vor externem API-Call freigeben
    db.close()

    from services.netlify_service import deploy_all_pages
    try:
        result = await deploy_all_pages(site_id, page_files, shared_css, "KOMPAGNON")
    except ValueError as e:
        # Token fehlt in der Env — HTTP 400 mit klarer Fehlermeldung
        logger.error(f"KAS Netlify Token fehlt: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"KAS Netlify deploy failed: {e}")
        raise HTTPException(502, f"KAS Deploy fehlgeschlagen: {str(e)[:200]}")

    # Deploy-Zeitstempel speichern (neue Session)
    from database import SessionLocal
    db2 = SessionLocal()
    try:
        _set_setting(db2, "kas_last_deploy", datetime.utcnow().isoformat(), user.id)
    finally:
        db2.close()

    logger.info(f"KAS deployed: {len(page_files)} pages, deploy_id={result['deploy_id']}")

    return {
        "deploy_id":      result["deploy_id"],
        "deploy_url":     result["deploy_url"],
        "state":          result["state"],
        "pages_deployed": list(page_files.keys()),
    }


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _serialize(p: KasPage, db: Session) -> dict:
    # has_content: schneller Lookup ohne Relationship-Lazy-Load
    has_content = db.query(KasGjsData.id).filter(
        KasGjsData.page_id == p.id,
        KasGjsData.html != "",
    ).first() is not None

    return {
        "id":               p.id,
        "titel":            p.titel,
        "pfad":             p.pfad,
        "meta_description": p.meta_description or "",
        "position":         p.position or 0,
        "status":           p.status or "draft",
        "ist_startseite":   bool(p.ist_startseite),
        "notizen":          p.notizen or "",
        "has_content":      has_content,
        "created_at":       str(p.created_at)[:16] if p.created_at else "",
        "updated_at":       str(p.updated_at)[:16] if p.updated_at else "",
    }


def _get_setting(db: Session, key: str) -> Optional[str]:
    row = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    return row.value if row else None


def _set_setting(db: Session, key: str, value: str, user_id: Optional[int] = None):
    row = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if row:
        row.value = value
        if user_id is not None:
            row.updated_by = user_id
    else:
        db.add(SystemSettings(key=key, value=value, updated_by=user_id))
    db.commit()
