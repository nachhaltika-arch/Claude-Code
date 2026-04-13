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
from routers.auth_router import require_admin, require_any_auth

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
def get_dashboard_kpis(
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Get KPI data for dashboard.

    Performance-optimiert:
      - audits_improved via 1 Aggregations-Query (vorher: N+1 mit Schleife ueber alle Leads)
      - Jeder Block in try/except gekapselt, damit eine einzelne kaputte
        Query nicht den ganzen Endpoint crasht (Security Fix 06 haette das
        sonst als generischen 500 zurueckgegeben)
    """
    # Defaults — alle Felder, die wir liefern MUESSEN (Pydantic-Modell)
    kpis = {
        "active_projects": 0,
        "average_margin_percent": 0,
        "projects_in_target": 0,
        "projects_at_risk": 0,
        "projects_going_live_this_week": 0,
        "pending_reviews": 0,
        "audits_today": 0,
        "audits_avg_score": 0,
        "audits_improved": 0,
        "leads_total": 0,
        "leads_won": 0,
    }

    # ── Margin-Summary ──────────────────────────────────────
    try:
        ms = MarginCalculator.get_margin_summary(db)
        kpis["active_projects"] = ms.get("active_projects", 0)
        kpis["average_margin_percent"] = ms.get("average_margin_percent", 0)
        kpis["projects_in_target"] = ms.get("projects_in_target", 0)
        kpis["projects_at_risk"] = ms.get("projects_at_risk", 0)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"dashboard/kpis margin_summary: {e}")

    # ── Projekte, die diese Woche live gehen ────────────────
    try:
        week_from_now = datetime.utcnow() + timedelta(days=7)
        kpis["projects_going_live_this_week"] = (
            db.query(Project)
            .filter(
                Project.status == "phase_6",
                Project.actual_go_live.isnot(None),
                Project.actual_go_live <= week_from_now,
            )
            .count()
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"dashboard/kpis golive: {e}")

    # ── Offene Reviews ──────────────────────────────────────
    try:
        kpis["pending_reviews"] = (
            db.query(Project)
            .filter(
                Project.status.in_(["phase_7", "completed"]),
                Project.review_received == False,
            )
            .count()
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"dashboard/kpis pending_reviews: {e}")

    # ── Audit KPIs ──────────────────────────────────────────
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        kpis["audits_today"] = (
            db.query(AuditResult)
            .filter(AuditResult.status == "completed", AuditResult.created_at >= today_start)
            .count()
        )
        avg_row = (
            db.query(func.avg(AuditResult.total_score))
            .filter(AuditResult.status == "completed")
            .scalar()
        )
        kpis["audits_avg_score"] = round(float(avg_row), 1) if avg_row else 0
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"dashboard/kpis audit_kpis: {e}")

    # ── audits_improved via 1 Aggregations-Query (war vorher N+1) ──
    # Nutzt PostgreSQL array_agg mit ORDER BY — neustes minus aeltestes Score
    # pro Lead, gezaehlt wird wer sich verbessert hat.
    try:
        row = db.execute(text("""
            SELECT COUNT(*) AS improved
            FROM (
                SELECT
                    lead_id,
                    (array_agg(total_score ORDER BY created_at ASC))[1]  AS first_score,
                    (array_agg(total_score ORDER BY created_at DESC))[1] AS last_score,
                    COUNT(*) AS n
                FROM audit_results
                WHERE lead_id IS NOT NULL AND status = 'completed'
                GROUP BY lead_id
                HAVING COUNT(*) >= 2
            ) sub
            WHERE last_score > first_score
        """)).fetchone()
        kpis["audits_improved"] = int(row.improved) if row and row.improved else 0
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"dashboard/kpis audits_improved: {e}")

    # ── Lead / Usercard counts ───────────────────────────────
    try:
        kpis["leads_total"] = db.query(Lead).count()
        kpis["leads_won"]   = db.query(Lead).filter(Lead.status == "won").count()
        if kpis["leads_total"] == 0:
            try:
                kpis["leads_total"] = db.execute(text("SELECT COUNT(*) FROM usercards")).scalar() or 0
                kpis["leads_won"]   = db.execute(text("SELECT COUNT(*) FROM usercards WHERE status = 'won'")).scalar() or 0
            except Exception:
                pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"dashboard/kpis lead_counts: {e}")

    return kpis


@router.get("/dashboard/alerts", response_model=list[Alert])
def get_dashboard_alerts(db: Session = Depends(get_db), _=Depends(require_any_auth)):
    """
    Get all active alerts for dashboard.

    Perf-optimiert (Fix Performance 03):
      - 1 SQL-Query + LEFT JOIN auf time_tracking, statt 1 + 2N ORM-Queries
      - Margin-Berechnung direkt im SQL (gleiche Formel wie MarginCalculator)
      - Kein ORM-Overhead — nur Tuples zum Klassifizieren
    """
    active_phases = ('phase_1', 'phase_2', 'phase_3', 'phase_4', 'phase_5', 'phase_6')

    rows = db.execute(text("""
        WITH project_costs AS (
            SELECT
                p.id,
                p.status,
                p.start_date,
                p.scope_creep_flags,
                COALESCE(p.fixed_price, :default_price) AS fixed_price,
                COALESCE(p.hourly_rate, :default_rate)  AS hourly_rate,
                COALESCE(p.ai_tool_costs, :default_ai)  AS ai_costs,
                COALESCE(
                    SUM(CASE WHEN t.logged_by <> 'KI' THEN t.hours ELSE 0 END),
                    0
                ) AS human_hours
            FROM projects p
            LEFT JOIN time_tracking t ON t.project_id = p.id
            WHERE p.status = ANY(:active_phases)
            GROUP BY p.id, p.status, p.start_date, p.scope_creep_flags,
                     p.fixed_price, p.hourly_rate, p.ai_tool_costs
        )
        SELECT
            id, status, start_date, scope_creep_flags, fixed_price,
            CASE
                WHEN fixed_price > 0 THEN
                    ((fixed_price - (human_hours * hourly_rate + ai_costs))
                     / fixed_price) * 100
                ELSE 0
            END AS margin_percent
        FROM project_costs
        ORDER BY id
    """), {
        "default_price": 2000.0,
        "default_rate":  45.0,
        "default_ai":    50.0,
        "active_phases": list(active_phases),
    }).fetchall()

    alerts: list[Alert] = []
    now = datetime.utcnow()

    for row in rows:
        # 1. Overdue phase (>3 days in same phase)
        if row.start_date:
            days_in_phase = (now - row.start_date).days
            if days_in_phase > 3:
                alerts.append(Alert(
                    alert_type="overdue_phase",
                    severity="warning" if days_in_phase < 5 else "critical",
                    project_id=row.id,
                    message=f"Projekt {row.id} seit {days_in_phase} Tagen in Phase {row.status}",
                    timestamp=now,
                ))

        # 2. Margin kritisch (rot = unter 70%, gleiche Schwelle wie MarginCalculator)
        margin_pct = float(row.margin_percent or 0)
        if margin_pct < 70:
            alerts.append(Alert(
                alert_type="margin_risk",
                severity="critical",
                project_id=row.id,
                message=f"Projekt {row.id}: Marge kritisch ({margin_pct:.1f}%)",
                timestamp=now,
            ))

        # 3. Scope Creep
        if (row.scope_creep_flags or 0) > 0:
            alerts.append(Alert(
                alert_type="scope_creep",
                severity="warning",
                project_id=row.id,
                message=f"Projekt {row.id}: {row.scope_creep_flags} Scope-Creep-Vorfälle",
                timestamp=now,
            ))

    return alerts


@router.get("/dashboard/projects-by-phase")
def get_projects_by_phase(db: Session = Depends(get_db), _=Depends(require_any_auth)):
    """
    Get projects grouped by phase (for kanban view).

    Perf-optimiert (Fix Performance 03):
      - 1 SQL-Query mit LEFT JOIN auf leads + time_tracking,
        statt 1 + 3N Queries (Projekt-Liste + pro Projekt:
        lead-Lazy-Load + 2x calculate_margin)
    """
    rows = db.execute(text("""
        WITH project_costs AS (
            SELECT
                p.id,
                p.status,
                p.start_date,
                p.margin_percent AS stored_margin,
                l.company_name   AS lead_company_name,
                COALESCE(p.fixed_price, :default_price) AS fixed_price,
                COALESCE(p.hourly_rate, :default_rate)  AS hourly_rate,
                COALESCE(p.ai_tool_costs, :default_ai)  AS ai_costs,
                COALESCE(
                    SUM(CASE WHEN t.logged_by <> 'KI' THEN t.hours ELSE 0 END),
                    0
                ) AS human_hours
            FROM projects p
            LEFT JOIN leads l           ON l.id = p.lead_id
            LEFT JOIN time_tracking t   ON t.project_id = p.id
            GROUP BY p.id, p.status, p.start_date, p.margin_percent,
                     l.company_name, p.fixed_price, p.hourly_rate, p.ai_tool_costs
        )
        SELECT
            id, status, start_date, stored_margin, lead_company_name,
            CASE
                WHEN fixed_price > 0 THEN
                    ((fixed_price - (human_hours * hourly_rate + ai_costs))
                     / fixed_price) * 100
                ELSE 0
            END AS computed_margin_percent
        FROM project_costs
        ORDER BY id
    """), {
        "default_price": 2000.0,
        "default_rate":  45.0,
        "default_ai":    50.0,
    }).fetchall()

    def _margin_status(pct: float) -> str:
        if pct >= 78:
            return "green"
        if pct >= 70:
            return "yellow"
        return "red"

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

    for row in rows:
        if row.status not in phases:
            continue
        phases[row.status].append({
            "id": row.id,
            "company_name": row.lead_company_name or "N/A",
            "margin_percent": row.stored_margin,
            "margin_status": _margin_status(float(row.computed_margin_percent or 0)),
            "started": row.start_date,
        })

    return {
        "phase_1_onboarding": phases["phase_1"],
        "phase_2_briefing":   phases["phase_2"],
        "phase_3_content":    phases["phase_3"],
        "phase_4_technik":    phases["phase_4"],
        "phase_5_qa":         phases["phase_5"],
        "phase_6_golive":     phases["phase_6"],
        "phase_7_postlaunch": phases["phase_7"],
        "completed":          phases["completed"],
    }


@router.get("/automations/jobs")
def get_active_jobs(_=Depends(require_admin)):
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
