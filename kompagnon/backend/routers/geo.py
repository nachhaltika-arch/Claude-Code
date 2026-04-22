"""
GEO/GAIO Router — Endpunkte fuer die KI-Sichtbarkeitsanalyse.

WICHTIG: Dieser Router registriert /api/geo/* Endpunkte.
Keine Ueberschneidung mit sitemap.py (registriert /api/sitemap/*).
"""

import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db, GeoAnalysis, Project
from routers.auth_router import require_any_auth, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/geo", tags=["geo"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _get_project_data(project_id: int, db: Session) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    lead = project.lead
    return {
        "website_url": getattr(lead, "website_url", "") or "",
        "gewerk": getattr(lead, "trade", "") or "Handwerk",
        "city": getattr(lead, "city", "") or "",
    }


@router.post("/{project_id}/analyze")
async def start_geo_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Startet GEO/GAIO Analyse fuer ein Projekt im Hintergrund."""
    project_data = _get_project_data(project_id, db)

    if not project_data["website_url"]:
        raise HTTPException(status_code=400, detail="Keine Website-URL im Projekt hinterlegt")

    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        analysis = GeoAnalysis(project_id=project_id, status="pending")
        db.add(analysis)
    else:
        analysis.status = "pending"
        analysis.error_message = None

    db.commit()
    db.refresh(analysis)
    analysis_id = analysis.id

    background_tasks.add_task(
        _run_analysis_background,
        analysis_id,
        project_id,
        project_data["website_url"],
        project_data["gewerk"],
        project_data["city"],
    )

    return {
        "status": "gestartet",
        "analysis_id": analysis_id,
        "message": "GEO-Analyse laeuft im Hintergrund (~30 Sekunden)",
    }


async def _run_analysis_background(
    analysis_id: int,
    project_id: int,
    website_url: str,
    gewerk: str,
    city: str,
):
    """Hintergrundtask: GEO-Analyse mit eigenen DB-Sessions."""
    from database import SessionLocal
    from services.geo_optimizer import GeoOptimizerAgent

    db = SessionLocal()
    try:
        analysis = db.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
        if not analysis:
            return
        analysis.status = "running"
        db.commit()
    finally:
        db.close()

    try:
        agent = GeoOptimizerAgent(api_key=ANTHROPIC_API_KEY)
        result = await agent.analyze(website_url, gewerk, city)

        db = SessionLocal()
        try:
            analysis = db.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
            if analysis:
                analysis.geo_score_total = result["geo_score_total"]
                analysis.llms_txt_score = result["llms_txt_score"]
                analysis.robots_ai_score = result["robots_ai_score"]
                analysis.structured_data_score = result["structured_data_score"]
                analysis.content_depth_score = result["content_depth_score"]
                analysis.local_signal_score = result["local_signal_score"]
                analysis.raw_checks = result["raw_checks"]
                analysis.recommendations = result["recommendations"]
                analysis.status = "done"
                analysis.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"GEO-Analyse {analysis_id} abgeschlossen: Score {result['geo_score_total']}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"GEO analysis background task failed: {type(e).__name__}: {e}")
        try:
            db_err = SessionLocal()
            try:
                a = db_err.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
                if a:
                    a.status = "failed"
                    a.error_message = str(e)[:500]
                    db_err.commit()
            finally:
                db_err.close()
        except Exception:
            pass


@router.get("/{project_id}/result")
def get_geo_result(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt das aktuelle GEO-Analyse-Ergebnis zurueck."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        return {"status": "not_started", "geo_score_total": None}

    return {
        "status": analysis.status,
        "geo_score_total": analysis.geo_score_total,
        "llms_txt_score": analysis.llms_txt_score,
        "robots_ai_score": analysis.robots_ai_score,
        "structured_data_score": analysis.structured_data_score,
        "content_depth_score": analysis.content_depth_score,
        "local_signal_score": analysis.local_signal_score,
        "recommendations": analysis.recommendations or [],
        "raw_checks": analysis.raw_checks or {},
        "upsell_active": analysis.upsell_active,
        "upsell_price": analysis.upsell_price,
        "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
        "error_message": analysis.error_message,
    }


@router.patch("/{project_id}/upsell")
def set_upsell(
    project_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Admin: Upsell-Paket aktivieren/deaktivieren und Preis setzen."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Noch keine GEO-Analyse vorhanden")

    if "upsell_active" in payload:
        analysis.upsell_active = bool(payload["upsell_active"])
    if "upsell_price" in payload:
        analysis.upsell_price = payload["upsell_price"]
    db.commit()

    return {
        "status": "ok",
        "upsell_active": analysis.upsell_active,
        "upsell_price": analysis.upsell_price,
    }
