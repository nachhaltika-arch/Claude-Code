"""
APScheduler setup for KOMPAGNON automation jobs.
Runs background jobs: daily checks, post-go-live follow-ups, triggers.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, Project
from services.margin_calculator import MarginCalculator
from services.email_service import EmailService, MockEmailService
from automations.email_templates import render_template
import logging

logger = logging.getLogger(__name__)


class CompagnonScheduler:
    """APScheduler wrapper for KOMPAGNON automation."""

    def __init__(self, database_url: str = "sqlite:///./kompagnon.db", use_mock_email: bool = False):
        jobstores = {
            "default": SQLAlchemyJobStore(url=database_url, tablename="apscheduler_jobs")
        }
        executors = {"default": ThreadPoolExecutor(max_workers=3)}

        self.scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
        self.use_mock_email = use_mock_email
        self.email_service = MockEmailService() if use_mock_email else EmailService()

    def start(self):
        """Start the scheduler and register all jobs."""
        self.scheduler.start()
        self._register_daily_jobs()
        logger.info("✓ Scheduler started with all daily jobs")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("✓ Scheduler stopped")

    def _register_daily_jobs(self):
        """Register jobs that run on fixed schedules."""
        # Daily at 08:00: Check overdue phases
        self.scheduler.add_job(
            self._check_overdue_phases,
            "cron",
            hour=8,
            minute=0,
            id="daily_check_overdue_phases",
            replace_existing=True,
            timezone="Europe/Berlin",
        )

        # Daily at 09:00: Check missing materials
        self.scheduler.add_job(
            self._check_missing_materials,
            "cron",
            hour=9,
            minute=0,
            id="daily_check_missing_materials",
            replace_existing=True,
            timezone="Europe/Berlin",
        )

        # Daily at 10:00: Update all margins
        self.scheduler.add_job(
            self._update_all_margins,
            "cron",
            hour=10,
            minute=0,
            id="daily_update_margins",
            replace_existing=True,
            timezone="Europe/Berlin",
        )

        logger.info("✓ Daily jobs registered")

    def trigger_phase_change(self, project_id: int, new_status: str):
        """
        Called when project phase changes (e.g., phase_1 → phase_2).
        Schedules corresponding follow-up jobs.
        """
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        db.close()

        if not project:
            return

        if new_status == "phase_2":
            # Payment received → welcome email
            self._send_phase_email(project_id, "welcome")

        elif new_status == "phase_6":
            # Go-live → schedule follow-ups
            self._schedule_golive_followups(project_id)

    def _schedule_golive_followups(self, project_id: int):
        """Schedule all post-go-live follow-up jobs."""
        # Day 5: Functionality check
        self.scheduler.add_job(
            self._tag_5_followup,
            "date",
            run_date=datetime.utcnow() + timedelta(days=5),
            args=[project_id],
            id=f"golive_day5_{project_id}",
            replace_existing=True,
        )
        logger.info(f"📅 Scheduled Day-5 check for Project {project_id}")

        # Day 14: Status report
        self.scheduler.add_job(
            self._tag_14_funktionscheck,
            "date",
            run_date=datetime.utcnow() + timedelta(days=14),
            args=[project_id],
            id=f"golive_day14_{project_id}",
            replace_existing=True,
        )
        logger.info(f"📅 Scheduled Day-14 check for Project {project_id}")

        # Day 21: Review request
        self.scheduler.add_job(
            self._tag_21_bewertungsanfrage,
            "date",
            run_date=datetime.utcnow() + timedelta(days=21),
            args=[project_id],
            id=f"golive_day21_{project_id}",
            replace_existing=True,
        )
        logger.info(f"📅 Scheduled Day-21 review request for Project {project_id}")

        # Day 30: GEO check + Upsell
        self.scheduler.add_job(
            self._tag_30_geo_check,
            "date",
            run_date=datetime.utcnow() + timedelta(days=30),
            args=[project_id],
            id=f"golive_day30_geo_{project_id}",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._tag_30_upsell,
            "date",
            run_date=datetime.utcnow() + timedelta(days=30, hours=1),
            args=[project_id],
            id=f"golive_day30_upsell_{project_id}",
            replace_existing=True,
        )
        logger.info(f"📅 Scheduled Day-30 jobs for Project {project_id}")

    # ===== DAILY JOBS =====

    def _check_overdue_phases(self):
        """Check projects stuck in phase > 2 days."""
        db = SessionLocal()
        projects = db.query(Project).filter(
            Project.status.in_(["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"])
        ).all()

        for project in projects:
            if project.start_date:
                days_in_phase = (datetime.utcnow() - project.start_date).days
                if days_in_phase > 2:
                    logger.warning(f"⚠️  Project {project.id} stuck in {project.status} for {days_in_phase} days")
                    # TODO: Send alert email to team

        db.close()

    def _check_missing_materials(self):
        """Check projects waiting for materials > 5 days."""
        db = SessionLocal()
        projects = db.query(Project).filter(Project.status == "phase_2").all()

        for project in projects:
            if project.start_date:
                days_since_start = (datetime.utcnow() - project.start_date).days
                if days_since_start > 5:
                    logger.info(f"📧 Sending material reminder for Project {project.id}")
                    # TODO: Send reminder email

        db.close()

    def _update_all_margins(self):
        """Recalculate margins for all active projects."""
        db = SessionLocal()
        projects = db.query(Project).filter(
            Project.status.in_(["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"])
        ).all()

        for project in projects:
            MarginCalculator.update_project_margin(db, project.id)
            logger.debug(f"💰 Margin updated for Project {project.id}")

        db.close()

    # ===== POST-GOLIVE JOBS =====

    def _tag_5_followup(self, project_id: int):
        """Day 5: Functionality check email."""
        logger.info(f"📧 Sending Day-5 check for Project {project_id}")
        self._send_phase_email(project_id, "day_5_followup")

    def _tag_14_funktionscheck(self, project_id: int):
        """Day 14: Status report."""
        logger.info(f"📧 Sending Day-14 report for Project {project_id}")
        self._send_phase_email(project_id, "day_14_check")

    def _tag_21_bewertungsanfrage(self, project_id: int):
        """Day 21: Review request (if not already received)."""
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()

        if project and not project.review_received:
            logger.info(f"📧 Sending review request for Project {project_id}")
            self._send_phase_email(project_id, "day_21_review_request")
        db.close()

    def _tag_30_geo_check(self, project_id: int):
        """Day 30: GEO check email."""
        logger.info(f"📧 Sending Day-30 GEO check for Project {project_id}")
        self._send_phase_email(project_id, "day_30_geo_check")

    def _tag_30_upsell(self, project_id: int):
        """Day 30: Upsell offer (if no upsell yet)."""
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()

        if project and project.customer and project.customer.upsell_status == "none":
            logger.info(f"📧 Sending upsell offer for Project {project_id}")
            self._send_phase_email(project_id, "day_30_upsell")
        db.close()

    # ===== HELPERS =====

    def _send_phase_email(self, project_id: int, template_key: str):
        """Send template email for a project."""
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project or not project.lead:
            db.close()
            return

        lead = project.lead
        context = {
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "assigned_person": "KOMPAGNON-Team",  # TODO: Read from settings
            "contact_person_phone": "+49 (0)123 456789",  # TODO: Read from settings
            "contact_person_email": "kontakt@kompagnon.de",  # TODO: Read from settings
            "preview_link": f"https://preview.example.de/{project_id}",
            "upload_link": f"https://app.example.de/upload/{project_id}",
            "review_deadline": (datetime.utcnow() + timedelta(days=3)).strftime("%d.%m.%Y"),
            "kickoff_date": (datetime.utcnow() + timedelta(days=2)).strftime("%d.%m.%Y"),
            "new_visitors": "42",
            "form_submissions": "3",
            "pagespeed_score": "87",
            "review_link": f"https://google.com/reviews/{project_id}",
        }

        try:
            rendered = render_template(template_key, context)
            success = self.email_service.send_email(
                to=lead.email,
                subject=rendered["subject"],
                body=rendered["body"],
            )

            if success:
                EmailService.log_communication(
                    db,
                    project_id,
                    "email",
                    "outbound",
                    rendered["subject"],
                    rendered["body"],
                    is_automated=True,
                    template_key=template_key,
                )
                logger.info(f"✓ Email sent for Project {project_id}: {template_key}")
            else:
                logger.error(f"✗ Email failed for Project {project_id}: {template_key}")

        except Exception as e:
            logger.error(f"✗ Error sending email: {str(e)}")

        db.close()


# Singleton scheduler instance
_scheduler = None


def get_scheduler(database_url: str = "sqlite:///./kompagnon.db", use_mock_email: bool = False):
    """Get or create scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = CompagnonScheduler(database_url, use_mock_email)
    return _scheduler


def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    if not scheduler.scheduler.running:
        scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler and _scheduler.scheduler.running:
        _scheduler.stop()
        _scheduler = None
