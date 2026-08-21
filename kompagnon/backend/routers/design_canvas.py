"""Design-Canvas: die vier KAS-Ansichten eines Betriebs aus- und wieder einlesen.

  GET  /api/design-canvas/{lead_id}         → Artboards + Anordnung
  POST /api/design-canvas/{lead_id}/import  → bearbeitete Artboards zurueck

**Warum ein eigener Weg neben den vier Ansichten.** Sitemap, Wireframe,
Style-Guide und Design haben je einen eigenen Editor im Werkzeug, und keiner
davon zeigt zwei Seiten nebeneinander. Der Canvas legt dieselben Daten auf eine
Flaeche. Er ersetzt die vier Ansichten nicht — er ist ein zweiter Zugang zu
denselben Zeilen.

**Was dieser Router nicht kann.** Er veroeffentlicht keinen Canvas. Dafuer gibt
es keine Schnittstelle: Ein Canvas entsteht in Claude Code und wird als
Artifact abgelegt. Dieser Router liefert die Dateien, aus denen er gebaut wird,
und nimmt sie bearbeitet zurueck — die beiden Enden, die im Werkzeug liegen.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Lead, Project, get_db
from routers.auth_router import require_innendienst
from routers.designs import DesignVersion
from routers.sitemap import SitemapPage
from services.design_canvas import baue, uebernimm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/design-canvas", tags=["design-canvas"],
                   dependencies=[Depends(require_innendienst)])


class CanvasImport(BaseModel):
    #: Dateiname → `.dc.html`-Quelltext, so wie der Canvas ihn haelt.
    files: dict


def _betrieb(db: Session, lead_id: int) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Betrieb nicht gefunden")
    return lead


def _seiten(db: Session, lead_id: int) -> list:
    zeilen = (db.query(SitemapPage)
                .filter(SitemapPage.lead_id == lead_id)
                .order_by(SitemapPage.position, SitemapPage.id)
                .all())
    return [{
        "id": z.id,
        "parent_id": z.parent_id,
        "position": z.position,
        "page_name": z.page_name,
        "page_type": z.page_type,
        "zweck": z.zweck,
        "ziel_keyword": z.ziel_keyword,
        "cta_text": z.cta_text,
        "cta_ziel": z.cta_ziel,
        "status": z.status,
        "mockup_html": z.mockup_html,
    } for z in zeilen]


@router.get("/{lead_id}")
def canvas_ausgeben(lead_id: int, db: Session = Depends(get_db)):
    """Die Artboards eines Betriebs — bereit zum Veroeffentlichen als Canvas."""
    lead = _betrieb(db, lead_id)
    project = (db.query(Project)
                 .filter(Project.lead_id == lead_id)
                 .order_by(Project.id.desc())
                 .first())
    ergebnis = baue(lead=lead, seiten=_seiten(db, lead_id), project=project)
    logger.info("Canvas ausgegeben: lead_id=%s, %s Artboards",
                lead_id, len(ergebnis["canvas"]["artboards"]))
    return {"lead_id": lead_id, "betrieb": lead.company_name, **ergebnis}


@router.post("/{lead_id}/import")
def canvas_uebernehmen(lead_id: int, body: CanvasImport, request: Request,
                       db: Session = Depends(get_db)):
    """Bearbeitete Design-Artboards auf die Kundenseiten schreiben.

    Jede geaenderte Seite bekommt vorher eine Zeile in `mockup_versions`. Wer
    im Canvas etwas verschlimmbessert, findet die vorige Fassung im
    Versionsverlauf wieder — dieselbe Liste, die auch die Design-Ansicht
    fuehrt.
    """
    _betrieb(db, lead_id)
    zeilen = {z.id: z for z in db.query(SitemapPage)
                                 .filter(SitemapPage.lead_id == lead_id).all()}

    uebernahmen = uebernimm(dateien=body.files, seiten_nach_id=zeilen)
    wer = request.headers.get("X-User") or request.headers.get("X-Username") or "Canvas"
    stempel = datetime.utcnow().strftime("%d.%m.%Y %H:%M")

    geaendert = []
    for eintrag in uebernahmen:
        zeile = zeilen[eintrag["page_id"]]
        if (zeile.mockup_html or "") == eintrag["markup"]:
            continue
        db.add(DesignVersion(
            lead_id=lead_id,
            sitemap_page_id=zeile.id,
            page_name=zeile.page_name or "",
            version_name=f"Aus dem Canvas, {stempel}",
            html_content=eintrag["markup"],
            created_by=wer,
        ))
        zeile.mockup_html = eintrag["markup"]
        geaendert.append({"page_id": zeile.id, "page_name": zeile.page_name})

    db.commit()
    logger.info("Canvas uebernommen: lead_id=%s, %s Seiten geaendert",
                lead_id, len(geaendert))
    return {
        "lead_id": lead_id,
        "gelesen": len(uebernahmen),
        "geaendert": geaendert,
    }
