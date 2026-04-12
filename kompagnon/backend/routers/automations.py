"""
Automation and Dashboard API routes.
GET /api/dashboard/kpis - Dashboard KPIs
GET /api/dashboard/alerts - Active alerts
POST /api/automations/trigger - Manual trigger
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import Project, Lead, Communication, AuditResult, get_db
from services.margin_calculator import MarginCalculator
from routers.auth_router import require_admin

router = APIRouter(prefix="/api", tags=["dashboard", "automations"])


class KPIData(BaseModel):
    active_projects: int
    average_margin_percent: float
    projects_in_target: int
    projects_at_risk: int
    projects_going_live_this_week: int
    pending_reviews: int
    audits_today: int = 0
    audits_avg_score: float = 0
    audits_improved: int = 0
    leads_total: int = 0
    leads_won: int = 0


class Alert(BaseModel):
    alert_type: str  # overdue_phase, scope_creep, margin_risk, missing_material
    severity: str  # info, warning, critical
    project_id: int
    message: str
    timestamp: datetime


@router.get("/dashboard/kpis", response_model=KPIData)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """Get KPI data for dashboard."""
    margin_summary = MarginCalculator.get_margin_summary(db)

    # Count projects going live this week
    week_from_now = datetime.utcnow() + timedelta(days=7)
    golive_this_week = (
        db.query(Project)
        .filter(
            Project.status == "phase_6",
            Project.actual_go_live.isnot(None),
            Project.actual_go_live <= week_from_now,
        )
        .count()
    )

    # Count projects pending reviews
    pending_reviews = (
        db.query(Project)
        .filter(
            Project.status.in_(["phase_7", "completed"]),
            Project.review_received == False,
        )
        .count()
    )

    # Audit KPIs
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    audits_today = (
        db.query(AuditResult)
        .filter(AuditResult.status == "completed", AuditResult.created_at >= today_start)
        .count()
    )
    avg_row = (
        db.query(func.avg(AuditResult.total_score))
        .filter(AuditResult.status == "completed")
        .scalar()
    )
    audits_avg_score = round(float(avg_row), 1) if avg_row else 0

    # Count leads that improved (have 2+ audits where latest > earliest)
    audits_improved = 0
    lead_ids_with_audits = (
        db.query(AuditResult.lead_id)
        .filter(AuditResult.lead_id.isnot(None), AuditResult.status == "completed")
        .group_by(AuditResult.lead_id)
        .having(func.count(AuditResult.id) >= 2)
        .all()
    )
    for (lid,) in lead_ids_with_audits:
        scores = (
            db.query(AuditResult.total_score)
            .filter(AuditResult.lead_id == lid, AuditResult.status == "completed")
            .order_by(AuditResult.created_at.asc())
            .all()
        )
        if len(scores) >= 2 and scores[-1][0] > scores[0][0]:
            audits_improved += 1

    # Lead / Usercard counts — prefer leads table, fallback to usercards
    leads_total = db.query(Lead).count()
    leads_won   = db.query(Lead).filter(Lead.status == "won").count()
    if leads_total == 0:
        try:
            leads_total = db.execute(text("SELECT COUNT(*) FROM usercards")).scalar() or 0
            leads_won   = db.execute(text("SELECT COUNT(*) FROM usercards WHERE status = 'won'")).scalar() or 0
        except Exception:
            pass

    return {
        "active_projects": margin_summary.get("active_projects", 0),
        "average_margin_percent": margin_summary.get("average_margin_percent", 0),
        "projects_in_target": margin_summary.get("projects_in_target", 0),
        "projects_at_risk": margin_summary.get("projects_at_risk", 0),
        "projects_going_live_this_week": golive_this_week,
        "pending_reviews": pending_reviews,
        "audits_today": audits_today,
        "audits_avg_score": audits_avg_score,
        "audits_improved": audits_improved,
        "leads_total": leads_total,
        "leads_won": leads_won,
    }


@router.get("/dashboard/alerts", response_model=list[Alert])
def get_dashboard_alerts(db: Session = Depends(get_db)):
    """Get all active alerts for dashboard."""
    alerts = []

    # Check for overdue phases (>3 days in phase)
    all_projects = db.query(Project).filter(
        Project.status.in_(
            ["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"]
        )
    ).all()

    for project in all_projects:
        if project.start_date:
            days_in_phase = (datetime.utcnow() - project.start_date).days
            if days_in_phase > 3:
                alerts.append(
                    Alert(
                        alert_type="overdue_phase",
                        severity="warning" if days_in_phase < 5 else "critical",
                        project_id=project.id,
                        message=f"Projekt {project.id} seit {days_in_phase} Tagen in Phase {project.status}",
                        timestamp=datetime.utcnow(),
                    )
                )

        # Check margin status
        margin = MarginCalculator.calculate_margin(db, project.id)
        if margin.get("status") == "red":
            alerts.append(
                Alert(
                    alert_type="margin_risk",
                    severity="critical",
                    project_id=project.id,
                    message=f"Projekt {project.id}: Marge kritisch ({margin.get('margin_percent', 0):.1f}%)",
                    timestamp=datetime.utcnow(),
                )
            )

        # Check for scope creep
        if project.scope_creep_flags > 0:
            alerts.append(
                Alert(
                    alert_type="scope_creep",
                    severity="warning",
                    project_id=project.id,
                    message=f"Projekt {project.id}: {project.scope_creep_flags} Scope-Creep-Vorfälle",
                    timestamp=datetime.utcnow(),
                )
            )

    return alerts


@router.get("/dashboard/projects-by-phase")
def get_projects_by_phase(db: Session = Depends(get_db)):
    """Get projects grouped by phase (for kanban view)."""
    phases = {
        "phase_1": [],
        "phase_2": [],
        "phase_3": [],
        "phase_4": [],
        "phase_5": [],
        "phase_6": [],
        "phase_7": [],
        "completed": [],
    }

    all_projects = db.query(Project).all()
    for project in all_projects:
        if project.status in phases:
            lead = project.lead
            phases[project.status].append(
                {
                    "id": project.id,
                    "company_name": lead.company_name if lead else "N/A",
                    "margin_percent": project.margin_percent,
                    "margin_status": MarginCalculator.calculate_margin(db, project.id).get("status"),
                    "started": project.start_date,
                }
            )

    return {
        "phase_1_onboarding": phases["phase_1"],
        "phase_2_briefing": phases["phase_2"],
        "phase_3_content": phases["phase_3"],
        "phase_4_technik": phases["phase_4"],
        "phase_5_qa": phases["phase_5"],
        "phase_6_golive": phases["phase_6"],
        "phase_7_postlaunch": phases["phase_7"],
        "completed": phases["completed"],
    }


@router.get("/automations/jobs")
def get_active_jobs():
    """Get list of active scheduled jobs."""
    from automations.scheduler import get_scheduler
    try:
        scheduler = get_scheduler()
        if not scheduler.scheduler.running:
            return {
                "active_jobs": 0,
                "jobs": [],
                "status": "scheduler_not_running",
                "info": "Scheduler wurde noch nicht gestartet oder ist auf Render nicht verfügbar.",
            }
        jobs = []
        for job in scheduler.scheduler.get_jobs():
            jobs.append({
                "job_id":   job.id,
                "name":     job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger":  str(job.trigger),
            })
        return {
            "active_jobs": len(jobs),
            "jobs": jobs,
            "status": "running",
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Jobs-Endpunkt Fehler: {e}", exc_info=True)
        return {
            "active_jobs": 0,
            "jobs": [],
            "status": "error",
            "info": "Jobs-Liste nicht verfügbar",
        }


@router.post("/automations/test-email")
def test_email(recipient: str = Query(...), _=Depends(require_admin)):
    """Testversand zur Verifizierung der SMTP-Konfiguration."""
    from services.email import send_test_email
    result = send_test_email(recipient)
    if not result["success"]:
        raise HTTPException(422, result.get("error", "Versand fehlgeschlagen"))
    return result
