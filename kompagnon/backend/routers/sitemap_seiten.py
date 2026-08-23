"""Eine einzelne Seite bearbeiten und pruefen (L-25).

**Warum eigene Datei, 22.08.2026.** Diese vier Routen hingen am
`pages_router` und lagen in `sitemap.py` — aber sie handeln von etwas
anderem: nicht von der **Struktur** einer Website, sondern vom **Inhalt**
einer einzelnen Seite. Editor laden, Editor speichern, Qualitaet pruefen,
Pruefungen nachlesen.

Sie teilten mit dem Rest nichts ausser `logger` und dem Router selbst.
"""
import json
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, Briefing, Lead, get_db
from routers.auth_router import require_any_auth, optional_auth, require_innendienst
# `GjsData` beschreibt die Nutzlast des Editors und steht in `sitemap.py`;
# geholt statt kopiert.
# `SitemapPage` ist ein SQLAlchemy-Modell **in `sitemap.py`**, nicht in
# `database.py` — ein `from database import SitemapPage` waere zur
# Laufzeit gescheitert, und ruff haette es nicht gemeldet: Er sieht,
# dass der Name definiert ist, nicht wo.
from routers.sitemap import GjsData, SitemapPage
import logging

logger = logging.getLogger(__name__)


# **Die Sperre haengt am Router (L-67, 22.08.2026).** Die fuenfzehn Routen
# hier fuehren die Seiten der Kundenprojekte samt Vorlagen — darunter
# `DELETE /{page_id}`, also das Entfernen einer Kundenseite. Sie verliessen
# sich auf `require_any_auth`; der `router` darueber traegt die Sperre seit
# jeher, dieser hier nicht.
#
# Vor der Sperre gemessen: `PageManager`, `PublicPageEditor` und
# `PageTemplateEditor` rufen die Adressen, alle unter
# `PrivateRoute roles={['admin']}`. Kein Aufruf aus dem Kundenportal.
pages_router = APIRouter(prefix="/api/pages", tags=["pages"],
                         dependencies=[Depends(require_innendienst)])


@pages_router.get("/{page_id}/editor")
def get_editor_data(
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    page = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    gjs_data = {}
    try:
        gjs_data = json.loads(page.gjs_data or '{}')
    except Exception:
        pass
    return {"html": page.gjs_html or "", "css": page.gjs_css or "", "gjsData": gjs_data}


@pages_router.post("/{page_id}/editor")
def save_editor_data(
    page_id: int,
    body: GjsData,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    page = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    page.gjs_html = body.html
    page.gjs_css  = body.css
    page.gjs_data = json.dumps(body.gjsData, ensure_ascii=False)
    db.commit()
    return {"ok": True}


@pages_router.post("/{page_id}/qualitaetspruefung")
async def qualitaetspruefung(
    page_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Prüft eine selbst gebaute Seite mit dem eigenen Katalog.

    Der Audit ist adressgetrieben, also bekommt die Seite zuerst eine Adresse:
    Sie wird auf die Vorschau-Site deployt, und das Audit läuft gegen diese
    Vorschau — nie gegen die Domain des Kunden, auf der noch der alte Auftritt
    steht.

    Schritt 8 des Design-Konzepts: Was wir Kunden vorwerfen, dürfen wir selbst
    nicht liefern.
    """
    from database import AuditResult
    from services.qualitaetsschleife import (
        KeineVorschauSite, NichtsZuPruefen, deploye_vorschau,
    )

    seite = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not seite:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")

    lead = db.query(Lead).filter(Lead.id == seite.lead_id).first()
    firmenname = (lead.display_name or lead.company_name) if lead else ""

    try:
        vorschau_url = await deploye_vorschau(seite, firmenname=firmenname or "")
    except NichtsZuPruefen as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeineVorschauSite as e:
        # Fehlende Einrichtung, kein Fehler im Ablauf — 503 sagt das.
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error(f"Qualitätsschleife: Deploy fehlgeschlagen: "
                     f"{type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Die Vorschau konnte nicht bereitgestellt werden: {e}")

    audit = AuditResult(
        lead_id=seite.lead_id,
        sitemap_page_id=seite.id,
        website_url=vorschau_url,
        company_name=firmenname or (seite.page_name or "Eigenprüfung"),
        city=(lead.city or "") if lead else "",
        status="pending",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    audit_id = audit.id

    from routers.audit import _run_audit_background
    background_tasks.add_task(_run_audit_background, audit_id)

    return {
        "audit_id": audit_id,
        "vorschau_url": vorschau_url,
        "status": "pending",
        "message": "Die Seite liegt als Vorschau bereit und wird geprüft.",
    }


@pages_router.get("/{page_id}/qualitaetspruefungen")
def qualitaetspruefungen(
    page_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Die bisherigen Eigenprüfungen dieser Seite, neueste zuerst."""
    from database import AuditResult

    laeufe = (
        db.query(AuditResult)
        .filter(AuditResult.sitemap_page_id == page_id)
        .order_by(AuditResult.created_at.desc())
        .limit(min(limit, 50))
        .all()
    )
    return [
        {
            "audit_id": a.id,
            "status": a.status,
            "total_score": a.total_score,
            "level": a.level,
            "coverage": a.coverage,
            "vorschau_url": a.website_url,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in laeufe
    ]
