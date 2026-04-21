"""
APScheduler setup for KOMPAGNON automation jobs.
Runs background jobs: daily checks, post-go-live follow-ups, triggers,
and weekly HWK lead scraping.

All job functions are module-level (standalone) to avoid serialization
issues with SQLAlchemyJobStore. APScheduler cannot serialize class
instances that contain a scheduler reference.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
from database import SessionLocal, Project, DATABASE_URL
from services.margin_calculator import MarginCalculator
from services.email import send_email
from services.email_service import EmailService
from automations.email_templates import render_template
import logging
import os

logger = logging.getLogger(__name__)

# Module-level config read once at import
_use_mock_email = os.getenv("USE_MOCK_EMAIL", "false").lower() == "true"


# ===================================================================
# STANDALONE JOB FUNCTIONS (no class instance references)
# ===================================================================

def _send_phase_email(project_id: int, template_key: str):
    """Send template email for a project (standalone function)."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project or not project.lead:
            return

        lead = project.lead
        context = {
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "assigned_person": "KOMPAGNON-Team",
            "contact_person_phone": "+49 (0)123 456789",
            "contact_person_email": "kontakt@kompagnon.de",
            "preview_link": f"https://preview.example.de/{project_id}",
            "upload_link": f"https://app.example.de/upload/{project_id}",
            "review_deadline": (datetime.utcnow() + timedelta(days=3)).strftime("%d.%m.%Y"),
            "kickoff_date": (datetime.utcnow() + timedelta(days=2)).strftime("%d.%m.%Y"),
            "new_visitors": "42",
            "form_submissions": "3",
            "pagespeed_score": "87",
            "review_link": f"https://google.com/reviews/{project_id}",
        }

        rendered = render_template(template_key, context)
        if _use_mock_email:
            logger.info(f"[MOCK] E-Mail an {lead.email}: {rendered['subject']}")
            success = True
        else:
            success = send_email(
                to_email=lead.email,
                subject=rendered["subject"],
                html_body=rendered["body"],
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
            logger.info(f"Email sent for Project {project_id}: {template_key}")
        else:
            logger.error(f"Email failed for Project {project_id}: {template_key}")

    except Exception as e:
        logger.error(f"✗ Error sending email: {str(e)}")
    finally:
        db.close()


# ----- HWK SCRAPER JOB -----

def job_enrich_pending_leads():
    """
    Daily lead enrichment job at 06:00 Europe/Berlin.
    Enriches up to 50 leads with analysis_score=0 and a website URL.
    """
    import asyncio
    logger.info("🔍 Daily lead enrichment job starting...")
    try:
        from database import SessionLocal
        from services.lead_enrichment import enrich_all_pending
        db = SessionLocal()
        try:
            results = asyncio.run(enrich_all_pending(db))
            logger.info(
                f"✓ Lead enrichment done: {results['success']} enriched, "
                f"{results['failed']} failed, {results['skipped']} skipped"
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"✗ Lead enrichment job failed: {e}")


def job_hwk_scrape_weekly():
    """
    Weekly HWK lead scraping job.
    Scrapes top 5 München trades with default city list.
    Runs every Monday at 02:00 Europe/Berlin.
    Set env HWK_SCRAPER_ENABLED=true to activate.
    """
    import os
    if os.getenv("HWK_SCRAPER_ENABLED", "false").lower() != "true":
        logger.info("⏭  HWK scraper job skipped (HWK_SCRAPER_ENABLED != true)")
        return

    logger.info("🔍 Weekly HWK scraper job starting...")
    try:
        from services.hwk_scraper import HwkScraperService
        service = HwkScraperService()
        result = service.run_default_batch()
        logger.info(
            f"✅ HWK scraper complete: "
            f"{result['leads_found']} found | {result['leads_saved']} saved"
        )
    except Exception as e:
        logger.error(f"❌ HWK scraper job failed: {e}", exc_info=True)


# ----- DAILY JOBS -----

def job_check_overdue_phases():
    """Check projects stuck in phase > 2 days."""
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(
            Project.status.in_(["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"])
        ).all()

        for project in projects:
            if project.start_date:
                days_in_phase = (datetime.utcnow() - project.start_date).days
                if days_in_phase > 2:
                    logger.warning(f"⚠️  Project {project.id} stuck in {project.status} for {days_in_phase} days")
    finally:
        db.close()


def job_check_missing_materials():
    """Check projects waiting for materials > 5 days."""
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.status == "phase_2").all()

        for project in projects:
            if project.start_date:
                days_since_start = (datetime.utcnow() - project.start_date).days
                if days_since_start > 5:
                    logger.info(f"📧 Sending material reminder for Project {project.id}")
                    _send_phase_email(project.id, "material_reminder")
    finally:
        db.close()


def job_update_all_margins():
    """Recalculate margins for all active projects."""
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(
            Project.status.in_(["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"])
        ).all()

        for project in projects:
            MarginCalculator.update_project_margin(db, project.id)
            logger.debug(f"💰 Margin updated for Project {project.id}")
    finally:
        db.close()


# ----- POST-GOLIVE JOBS -----

def job_tag_5_followup(project_id: int):
    """Day 5: Functionality check email."""
    logger.info(f"📧 Sending Day-5 check for Project {project_id}")
    _send_phase_email(project_id, "day_5_followup")


def job_tag_14_funktionscheck(project_id: int):
    """Day 14: Status report."""
    logger.info(f"📧 Sending Day-14 report for Project {project_id}")
    _send_phase_email(project_id, "day_14_check")


def job_tag_21_bewertungsanfrage(project_id: int):
    """Day 21: Review request (if not already received)."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and not project.review_received:
            logger.info(f"📧 Sending review request for Project {project_id}")
            _send_phase_email(project_id, "day_21_review_request")
    finally:
        db.close()


def job_tag_30_geo_check(project_id: int):
    """Day 30: GEO check email."""
    logger.info(f"📧 Sending Day-30 GEO check for Project {project_id}")
    _send_phase_email(project_id, "day_30_geo_check")


def job_tag_30_upsell(project_id: int):
    """Day 30: Upsell offer (if no upsell yet)."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and project.customer and project.customer.upsell_status == "none":
            logger.info(f"📧 Sending upsell offer for Project {project_id}")
            _send_phase_email(project_id, "day_30_upsell")
    finally:
        db.close()


async def _check_all_domains_async():
    from database import SessionLocal, Lead, Project
    from services.domain_checker import check_domain
    from datetime import datetime
    db = SessionLocal()
    try:
        leads = db.query(Lead).filter(Lead.website_url != None,
                                      Lead.website_url != "").all()
        for lead in leads:
            try:
                result = await check_domain(lead.website_url)
                lead.domain_reachable   = result["reachable"]
                lead.domain_status_code = result.get("status_code")
                lead.domain_checked_at  = datetime.utcnow()
            except Exception:
                pass
        db.commit()

        projects = db.query(Project).filter(Project.website_url != None,
                                            Project.website_url != "").all()
        for project in projects:
            try:
                result = await check_domain(project.website_url)
                project.domain_reachable   = result["reachable"]
                project.domain_status_code = result.get("status_code")
                project.domain_checked_at  = datetime.utcnow()
            except Exception:
                pass
        db.commit()
    finally:
        db.close()


def job_check_netlify_dns():
    """Check DNS status for active Netlify projects with backoff on 429."""
    import random
    import time as _time
    from datetime import datetime, timedelta
    from sqlalchemy import text as _text

    db = SessionLocal()
    now = datetime.utcnow()

    try:
        rows = db.execute(_text("""
            SELECT id, netlify_site_id, company_name,
                   netlify_dns_fail_count, netlify_dns_retry_after
            FROM projects
            WHERE netlify_site_id IS NOT NULL
              AND (domain_reachable IS NULL OR domain_reachable = false)
              AND (netlify_dns_retry_after IS NULL OR netlify_dns_retry_after < :now)
            ORDER BY id
            LIMIT 50
        """), {"now": now}).fetchall()

        if not rows:
            logger.info("DNS-Polling: Keine Projekte zu pruefen")
            return

        logger.info(f"DNS-Polling: {len(rows)} Projekte zu pruefen")

        NETLIFY_TOKEN = os.getenv("NETLIFY_API_TOKEN", "")
        if not NETLIFY_TOKEN:
            logger.warning("DNS-Polling: NETLIFY_API_TOKEN nicht gesetzt")
            return

        import httpx

        for row in rows:
            project_id   = row[0]
            site_id      = row[1]
            company_name = row[2] or f"Projekt {project_id}"
            fail_count   = row[3] or 0

            _time.sleep(random.uniform(0, 3))

            try:
                resp = httpx.get(
                    f"https://api.netlify.com/api/v1/sites/{site_id}",
                    headers={"Authorization": f"Bearer {NETLIFY_TOKEN}"},
                    timeout=10.0,
                )

                if resp.status_code == 429:
                    new_fail_count = fail_count + 1
                    backoff_minutes = min(10 * (2 ** fail_count), 1440)
                    retry_after = now + timedelta(minutes=backoff_minutes)

                    db.execute(_text("""
                        UPDATE projects
                        SET netlify_dns_fail_count = :fc,
                            netlify_dns_retry_after = :ra
                        WHERE id = :id
                    """), {"fc": new_fail_count, "ra": retry_after, "id": project_id})
                    db.commit()

                    logger.warning(
                        f"DNS-Polling: Projekt {project_id} ({company_name}) — "
                        f"429 Rate-Limited. Backoff: {backoff_minutes}min"
                    )
                    continue

                if resp.status_code != 200:
                    logger.warning(f"DNS-Polling: Projekt {project_id} — Netlify API {resp.status_code}")
                    continue

                data = resp.json()
                ssl_ready = data.get("ssl") is not None
                published = data.get("published_deploy", {})
                domain_reachable = ssl_ready and published.get("state") == "ready"

                db.execute(_text("""
                    UPDATE projects
                    SET domain_reachable = :reachable,
                        netlify_dns_fail_count = 0,
                        netlify_dns_retry_after = NULL,
                        updated_at = :now
                    WHERE id = :id
                """), {"reachable": domain_reachable, "now": now, "id": project_id})
                db.commit()

                status = "erreichbar" if domain_reachable else "noch nicht erreichbar"
                logger.info(f"DNS-Polling: Projekt {project_id} ({company_name}) — {status}")

            except Exception as e:
                logger.error(f"DNS-Polling: Projekt {project_id} Fehler: {type(e).__name__}: {e}")
                try:
                    db.rollback()
                except Exception:
                    pass

    finally:
        db.close()


def job_check_all_domains():
    import asyncio
    logger.info("🌐 Domain-Check gestartet...")
    asyncio.run(_check_all_domains_async())
    logger.info("✓ Domain-Check abgeschlossen")


# ===================================================================
# SCHEDULER CLASS (thin wrapper, no job logic)
# ===================================================================

class CompagnonScheduler:
    """APScheduler wrapper for KOMPAGNON automation."""

    def __init__(self, database_url: str = None, use_mock_email: bool = False):
        database_url = database_url or DATABASE_URL
        global _use_mock_email
        _use_mock_email = use_mock_email

        # JobStore mit Fallback auf MemoryJobStore wenn DB nicht erreichbar
        try:
            from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
            jobstores = {
                "default": SQLAlchemyJobStore(
                    url=database_url,
                    tablename="apscheduler_jobs"
                )
            }
        except Exception as e:
            logger.warning(f"⚠ SQLAlchemy JobStore nicht verfügbar ({e}) — nutze MemoryJobStore")
            from apscheduler.jobstores.memory import MemoryJobStore
            jobstores = {"default": MemoryJobStore()}

        executors = {"default": ThreadPoolExecutor(max_workers=3)}
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors
        )

    def start(self):
        """Start the scheduler and register all daily jobs."""
        self.scheduler.start()
        self._register_daily_jobs()
        logger.info("✓ Scheduler started with all daily jobs")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("✓ Scheduler stopped")

    def _register_daily_jobs(self):
        """Register cron jobs using standalone functions."""
        self.scheduler.add_job(
            job_check_all_domains,
            "interval", hours=6,
            id="domain_check_every_6h",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_check_overdue_phases,
            "cron",
            hour=8, minute=0,
            id="daily_check_overdue_phases",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        self.scheduler.add_job(
            job_check_missing_materials,
            "cron",
            hour=9, minute=0,
            id="daily_check_missing_materials",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        self.scheduler.add_job(
            job_update_all_margins,
            "cron",
            hour=10, minute=0,
            id="daily_update_margins",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        # Daily lead enrichment — 06:00
        self.scheduler.add_job(
            job_enrich_pending_leads,
            "cron",
            hour=6, minute=0,
            id="daily_enrich_leads",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        # Weekly HWK lead scraping — Mondays at 02:00
        self.scheduler.add_job(
            job_hwk_scrape_weekly,
            "cron",
            day_of_week="mon",
            hour=2, minute=0,
            id="weekly_hwk_scraper",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        self.scheduler.add_job(
            job_check_netlify_dns,
            "interval", minutes=15,
            id="netlify_dns_check_every_15min",
            replace_existing=True,
        )
        logger.info("Daily jobs registered (incl. weekly HWK scraper, Netlify DNS)")

        # Stündlicher E-Mail-Sequenz-Runner
        try:
            from services.sequence_runner import run_email_sequences
            self.scheduler.add_job(
                run_email_sequences,
                "interval",
                hours=1,
                id="email_sequence_runner",
                replace_existing=True,
            )
            logger.info("✓ E-Mail-Sequenz-Job registriert (stündlich)")
        except Exception as e:
            logger.warning(f"⚠ E-Mail-Sequenz-Job nicht registriert: {e}")

    def trigger_phase_change(self, project_id: int, new_status: str):
        """Called when project phase changes. Schedules follow-up jobs."""
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        db.close()

        if not project:
            return

        if new_status == "phase_2":
            _send_phase_email(project_id, "welcome")

        elif new_status == "phase_6":
            self._schedule_golive_followups(project_id)

    def _schedule_golive_followups(self, project_id: int):
        """Schedule all post-go-live follow-up jobs using standalone functions."""
        self.scheduler.add_job(
            job_tag_5_followup,
            "date",
            run_date=datetime.utcnow() + timedelta(days=5),
            args=[project_id],
            id=f"golive_day5_{project_id}",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_tag_14_funktionscheck,
            "date",
            run_date=datetime.utcnow() + timedelta(days=14),
            args=[project_id],
            id=f"golive_day14_{project_id}",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_tag_21_bewertungsanfrage,
            "date",
            run_date=datetime.utcnow() + timedelta(days=21),
            args=[project_id],
            id=f"golive_day21_{project_id}",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_tag_30_geo_check,
            "date",
            run_date=datetime.utcnow() + timedelta(days=30),
            args=[project_id],
            id=f"golive_day30_geo_{project_id}",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_tag_30_upsell,
            "date",
            run_date=datetime.utcnow() + timedelta(days=30, hours=1),
            args=[project_id],
            id=f"golive_day30_upsell_{project_id}",
            replace_existing=True,
        )
        logger.info(f"📅 Scheduled all post-go-live jobs for Project {project_id}")


# ===================================================================
# MODULE-LEVEL SINGLETON & HELPERS
# ===================================================================

_scheduler = None


def get_scheduler(database_url: str = None, use_mock_email: bool = False):
    """Get or create scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = CompagnonScheduler(database_url, use_mock_email)
    return _scheduler


def start_scheduler():
    """Start the global scheduler. Fehler werden nur geloggt."""
    global _scheduler
    try:
        scheduler = get_scheduler()
        if not scheduler.scheduler.running:
            scheduler.start()
            logger.info("✓ Scheduler gestartet")
        else:
            logger.info("✓ Scheduler läuft bereits")
    except Exception as e:
        logger.warning(
            f"⚠ Scheduler konnte nicht gestartet werden: {e} "
            f"— Automatische Jobs deaktiviert, App läuft weiter."
        )
        # _scheduler NICHT auf None zurücksetzen —
        # get_active_jobs() soll trotzdem antworten können


def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler and _scheduler.scheduler.running:
        _scheduler.stop()
        _scheduler = None
