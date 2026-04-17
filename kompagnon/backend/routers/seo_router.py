"""
SEO-Analyse Router
POST /api/seo/trigger/{project_id}  — Startet KI-SEO-Analyse als BackgroundTask
GET  /api/seo/result/{project_id}   — Gibt gespeichertes Ergebnis zurueck
"""
import json
import logging
import os
import re as _re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from routers.auth_router import require_any_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/seo", tags=["seo"])


def _generate_seo_analysis(
    trade: str, city: str, company_name: str, url: str, radius_km: int = 25,
) -> dict:
    """Synchroner Claude-Call fuer die SEO-Analyse. Gibt strukturiertes JSON zurueck."""
    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")

    prompt = (
        "Du bist ein erfahrener lokaler SEO-Experte fuer deutsche Handwerksbetriebe.\n\n"
        f"Analysiere: {company_name}\nGewerk: {trade}\nOrt: {city}\n"
        f"Website: {url or 'nicht angegeben'}\nEinzugsgebiet: {radius_km} km\n\n"
        "Antworte NUR mit validem JSON (kein Markdown). Struktur:\n"
        '{"overall_score":<0-100>,"keyword_score":<0-100>,"onpage_score":<0-100>,'
        '"competitor_score":<0-100>,'
        '"top_keywords":[{"keyword":"...","type":"Hauptkeyword|Lokal-Intent|Transaktional|Service|Informational|Trust|Qualitaet|Dringlichkeit","priority":"hoch|mittel|niedrig","volume":<0-100>}],'
        '"onpage_issues":[{"status":"ok|warn|err","label":"...","description":"..."}],'
        '"competitors":[{"name":"...","score":<0-100>}],'
        '"action_plan":[{"title":"...","time":"...","effect":"..."}]}\n\n'
        f"Ersetze alle Platzhalter durch echte Werte fuer {trade} in {city}. "
        "Variiere Scores realistisch (35-70 fuer typischen Betrieb ohne aktive SEO)."
    )

    client = Anthropic(api_key=api_key, max_retries=0, timeout=60.0)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = _re.sub(r"^```json\s*", "", raw)
    raw = _re.sub(r"^```\s*", "", raw)
    raw = _re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def run_seo_analysis_background(
    project_id: int,
    trade: str,
    city: str,
    company_name: str,
    url: str,
    radius_km: int,
) -> None:
    """Laeuft als BackgroundTask mit eigener DB-Session (Pool-Safety)."""
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE seo_analyses SET status = 'running', updated_at = NOW() WHERE project_id = :pid"),
            {"pid": project_id},
        )
        db.commit()

        result = _generate_seo_analysis(trade, city, company_name, url, radius_km)

        db.execute(
            text("""
                UPDATE seo_analyses SET
                    overall_score    = :overall_score,
                    keyword_score    = :keyword_score,
                    onpage_score     = :onpage_score,
                    competitor_score = :competitor_score,
                    top_keywords     = :top_keywords,
                    onpage_issues    = :onpage_issues,
                    competitors      = :competitors,
                    action_plan      = :action_plan,
                    status           = 'completed',
                    updated_at       = NOW()
                WHERE project_id = :pid
            """),
            {
                "pid": project_id,
                "overall_score":    result.get("overall_score"),
                "keyword_score":    result.get("keyword_score"),
                "onpage_score":     result.get("onpage_score"),
                "competitor_score": result.get("competitor_score"),
                "top_keywords":     json.dumps(result.get("top_keywords", []), ensure_ascii=False),
                "onpage_issues":    json.dumps(result.get("onpage_issues", []), ensure_ascii=False),
                "competitors":      json.dumps(result.get("competitors", []), ensure_ascii=False),
                "action_plan":      json.dumps(result.get("action_plan", []), ensure_ascii=False),
            },
        )
        db.commit()
        logger.info(f"SEO analysis completed for project {project_id}")

    except Exception as e:
        logger.error(f"SEO analysis failed for project {project_id}: {e}")
        try:
            db.execute(
                text("UPDATE seo_analyses SET status='failed', error_message=:err, updated_at=NOW() WHERE project_id=:pid"),
                {"pid": project_id, "err": str(e)[:500]},
            )
            db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


@router.post("/trigger/{project_id}")
def trigger_seo_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Startet eine SEO-Analyse als BackgroundTask."""
    from database import Project, Lead

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead = db.query(Lead).filter(Lead.id == project.lead_id).first()

    trade        = (lead.trade if lead else "") or "Handwerk"
    city         = (lead.city if lead else "") or ""
    company_name = (lead.company_name if lead else "") or "Unbekannt"
    url          = (lead.website_url if lead else "") or ""

    existing = db.execute(
        text("SELECT id FROM seo_analyses WHERE project_id = :pid"), {"pid": project_id},
    ).fetchone()

    if not existing:
        db.execute(
            text("""
                INSERT INTO seo_analyses (project_id, trade, city, radius_km, status)
                VALUES (:pid, :trade, :city, 25, 'pending')
            """),
            {"pid": project_id, "trade": trade, "city": city},
        )
        db.commit()
    else:
        db.execute(
            text("UPDATE seo_analyses SET status='pending', error_message=NULL, updated_at=NOW() WHERE project_id=:pid"),
            {"pid": project_id},
        )
        db.commit()

    # DB freigeben vor BackgroundTask
    db.close()

    background_tasks.add_task(
        run_seo_analysis_background,
        project_id, trade, city, company_name, url, 25,
    )

    return {"message": "SEO-Analyse gestartet", "project_id": project_id, "status": "running"}


@router.get("/result/{project_id}")
def get_seo_result(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt das gespeicherte SEO-Analyse-Ergebnis zurueck."""
    result = db.execute(
        text("SELECT * FROM seo_analyses WHERE project_id = :pid ORDER BY created_at DESC LIMIT 1"),
        {"pid": project_id},
    ).fetchone()

    if not result:
        return {"status": "not_found", "message": "Noch keine SEO-Analyse vorhanden"}

    return {
        "id":               result.id,
        "project_id":       result.project_id,
        "status":           result.status,
        "created_at":       str(result.created_at) if result.created_at else None,
        "updated_at":       str(result.updated_at) if result.updated_at else None,
        "trade":            result.trade,
        "city":             result.city,
        "overall_score":    result.overall_score,
        "keyword_score":    result.keyword_score,
        "onpage_score":     result.onpage_score,
        "competitor_score": result.competitor_score,
        "top_keywords":     result.top_keywords or [],
        "onpage_issues":    result.onpage_issues or [],
        "competitors":      result.competitors or [],
        "action_plan":      result.action_plan or [],
        "error_message":    result.error_message,
    }


@router.get("/result/by-lead/{lead_id}")
def get_seo_result_by_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt das neueste SEO-Ergebnis fuer einen Lead zurueck (ueber dessen Projekt)."""
    result = db.execute(
        text("""
            SELECT sa.* FROM seo_analyses sa
            JOIN projects p ON p.id = sa.project_id
            WHERE p.lead_id = :lid
            ORDER BY sa.created_at DESC
            LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()

    if not result:
        return {"status": "not_found"}

    return {
        "id":               result.id,
        "project_id":       result.project_id,
        "status":           result.status,
        "created_at":       str(result.created_at) if result.created_at else None,
        "updated_at":       str(result.updated_at) if result.updated_at else None,
        "trade":            result.trade,
        "city":             result.city,
        "overall_score":    result.overall_score,
        "keyword_score":    result.keyword_score,
        "onpage_score":     result.onpage_score,
        "competitor_score": result.competitor_score,
        "top_keywords":     result.top_keywords or [],
        "onpage_issues":    result.onpage_issues or [],
        "competitors":      result.competitors or [],
        "action_plan":      result.action_plan or [],
        "error_message":    result.error_message,
    }
