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
from services.email_service import EmailService, MockEmailService
from automations.email_templates import render_template
import logging
import os

logger = logging.getLogger(__name__)

# Module-level config read once at import
_use_mock_email = os.getenv("USE_MOCK_EMAIL", "false").lower() == "true"


# ===================================================================
# STANDALONE JOB FUNCTIONS (no class instance references)
# ===================================================================

def _get_email_service():
    """Create a fresh email service instance per job execution."""
    if _use_mock_email:
        return MockEmailService()
    return EmailService()


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
        email_service = _get_email_service()
        success = email_service.send_email(
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
    Toggled via POST /api/scraper/schedule or env HWK_SCRAPER_ENABLED=true.
    """
    try:
        from routers.scraper import is_schedule_enabled
        enabled = is_schedule_enabled()
    except Exception:
        import os
        enabled = os.getenv("HWK_SCRAPER_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("⏭  HWK scraper job skipped (schedule disabled)")
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
        result_summary = (
            f"HWK Wochenscraper abgeschlossen: "
            f"{result['leads_found']} gefunden, "
            f"{result['leads_saved']} gespeichert, "
            f"{result.get('errors', 0)} Fehler"
        )
        logger.info(result_summary)
    except Exception as e:
        logger.error(f"❌ HWK scraper job failed: {e}", exc_info=True)


# ----- DAILY JOBS -----

def job_check_netlify_dns():
    """Prüft alle 10 Min. ob Custom Domains mit pending-Status nun auf Netlify zeigen."""
    from sqlalchemy import text
    try:
        from services.netlify_service import check_dns_active
    except Exception as e:
        logger.warning(f"Netlify DNS-Check: service import fehlgeschlagen: {e}")
        return

    db = SessionLocal()
    try:
        pending = db.execute(text("""
            SELECT id, netlify_domain, netlify_site_url, lead_id
            FROM projects
            WHERE netlify_domain IS NOT NULL
              AND netlify_domain_status = 'pending'
        """)).fetchall()

        for p in pending:
            try:
                if check_dns_active(p.netlify_domain, p.netlify_site_url or ""):
                    db.execute(text("""
                        UPDATE projects SET
                          netlify_domain_status = 'active',
                          netlify_ssl_active    = TRUE,
                          updated_at            = NOW()
                        WHERE id = :id
                    """), {"id": p.id})
                    # Portal-Benachrichtigung
                    try:
                        db.execute(text("""
                            INSERT INTO messages (lead_id, channel, content, direction, created_at, sender_role)
                            VALUES (:lead_id, 'in_app', :content, 'outbound', NOW(), 'system')
                        """), {
                            "lead_id": p.lead_id,
                            "content": (
                                f"🎉 Ihre Website ist jetzt unter {p.netlify_domain} live! "
                                f"Das SSL-Zertifikat wird automatisch innerhalb weniger Minuten aktiviert."
                            ),
                        })
                    except Exception as me:
                        logger.warning(f"DNS-Live-Nachricht Fehler Projekt {p.id}: {me}")
                    logger.info(f"✓ DNS aktiv: {p.netlify_domain} (Projekt {p.id})")
            except Exception as pe:
                logger.warning(f"DNS-Check Projekt {p.id} Fehler: {pe}")
                continue
        db.commit()
    except Exception as e:
        logger.error(f"Netlify DNS-Check Fehler: {e}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def job_check_overdue_phases():
    """Check projects stuck in phase > 2 days and create a support ticket after 3 days."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(
            Project.status.in_(["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"])
        ).all()

        for project in projects:
            try:
                if not project.start_date:
                    continue
                days_in_phase = (datetime.utcnow() - project.start_date).days
                if days_in_phase <= 2:
                    continue

                logger.warning(f"⚠️  Project {project.id} stuck in {project.status} for {days_in_phase} days")

                # Nach 3 Tagen: internes Ticket erstellen (nur einmal pro Projekt+Phase+Tag)
                if days_in_phase >= 3:
                    ticket_key = f"stuck-{project.id}-{project.status}-{datetime.utcnow().strftime('%Y%m%d')}"
                    existing = db.execute(text(
                        "SELECT id FROM support_tickets WHERE ticket_number = :key LIMIT 1"
                    ), {"key": ticket_key}).fetchone()
                    if not existing:
                        db.execute(text("""
                            INSERT INTO support_tickets
                                (ticket_number, type, priority, status, title, description, user_email, user_name)
                            VALUES
                                (:nr, 'system', 'medium', 'open', :title, :desc, '', 'System')
                        """), {
                            "nr":    ticket_key,
                            "title": f"Projekt {project.id} feststeckend in {project.status}",
                            "desc":  f"Projekt {project.id} ({project.company_name or '—'}) ist seit {days_in_phase} Tagen in Phase {project.status}. Bitte prüfen.",
                        })
                        db.commit()
                        logger.info(f"✓ Stuck-Phase Ticket erstellt für Projekt {project.id}")
            except Exception as e:
                logger.error(f"Stuck-Phase Check Fehler für Projekt {getattr(project, 'id', '?')}: {e}")
                try:
                    db.rollback()
                except Exception:
                    pass
                continue
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


def job_check_all_domains():
    import asyncio
    logger.info("🌐 Domain-Check gestartet...")
    asyncio.run(_check_all_domains_async())
    logger.info("✓ Domain-Check abgeschlossen")


def job_cleanup_revoked_tokens():
    """Taeglich: abgelaufene Token-Blacklist-Eintraege loeschen."""
    from database import SessionLocal, RevokedToken
    db = SessionLocal()
    try:
        deleted = db.query(RevokedToken).filter(
            RevokedToken.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        if deleted:
            logger.info(f"🧹 {deleted} abgelaufene Token-Blacklist-Eintraege geloescht")
    except Exception as e:
        logger.error(f"Token-Cleanup fehlgeschlagen: {e}")
    finally:
        db.close()


def job_briefing_approval_reminders():
    """Stuendlicher Job: prueft eingereichte, aber nicht freigegebene Briefings.

    - 24h <= Wartezeit < 25h: Erinnerungs-Mail an Admin (genau einmal, da
      der Job stuendlich laeuft und das 1h-Fenster damit jede Entry exakt
      einmal trifft).
    - >= 48h:                 Eskalations-Mail an Admin (warnt jede Stunde
      bis zur Freigabe — bewusst noisy, damit es nicht ignoriert wird).

    Hinweis: In diesem Commit werden die E-Mails noch als WARNING/ERROR
    in den Logger geschrieben. Das tatsaechliche Versenden ist als TODO
    markiert und wird in einem Folge-Commit ergaenzt, sobald SMTP-Config
    + Template-Runner abgestimmt sind.
    """
    from sqlalchemy import text as _text
    db = SessionLocal()
    try:
        pending = db.execute(_text("""
            SELECT p.id AS project_id,
                   p.lead_id AS lead_id,
                   p.briefing_submitted_at AS briefing_submitted_at,
                   COALESCE(l.company_name, l.display_name, '') AS company,
                   COALESCE(l.email, '') AS email
            FROM projects p
            LEFT JOIN leads l ON l.id = p.lead_id
            WHERE p.briefing_submitted_at IS NOT NULL
              AND p.briefing_approved_at IS NULL
        """)).fetchall()

        if not pending:
            return

        now = datetime.utcnow()
        reminders_sent = 0
        escalations_sent = 0
        for row in pending:
            submitted_at = row.briefing_submitted_at
            if not submitted_at:
                continue
            hours_waiting = (now - submitted_at).total_seconds() / 3600.0

            if 24 <= hours_waiting < 25:
                reminders_sent += 1
                logger.warning(
                    f"⏰ Briefing-Reminder: Projekt {row.project_id} "
                    f"({row.company or 'unbekannt'}) wartet seit "
                    f"{int(hours_waiting)}h auf Admin-Freigabe."
                )
                # TODO: Admin-E-Mail (services/email_service.EmailService)
                # wird in einem separaten Commit ergaenzt — Template ist
                # noch nicht finalisiert.

            elif hours_waiting >= 48:
                escalations_sent += 1
                logger.error(
                    f"🚨 ESKALATION: Briefing fuer Projekt {row.project_id} "
                    f"({row.company or 'unbekannt'}) wartet seit "
                    f"{int(hours_waiting)}h auf Admin-Freigabe!"
                )
                # TODO: Eskalations-Mail an Admin + Support-Verteiler.

        if reminders_sent or escalations_sent:
            logger.info(
                f"briefing_approval_reminders: {reminders_sent} Reminder, "
                f"{escalations_sent} Eskalationen (total pending: {len(pending)})"
            )
    except Exception as e:
        logger.error(f"briefing_approval_reminders Job Fehler: {e}")
    finally:
        db.close()


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
            job_check_netlify_dns,
            "interval", minutes=10,
            id="netlify_dns_check_every_10min",
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
        # Daily cleanup of revoked JWT tokens — 03:00
        self.scheduler.add_job(
            job_cleanup_revoked_tokens,
            "cron",
            hour=3, minute=0,
            id="daily_cleanup_revoked_tokens",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        # Stuendlicher Briefing-Approval-Reminder — Tor 1 der
        # Funnel-Automation. Prueft projects mit
        # briefing_submitted_at IS NOT NULL AND briefing_approved_at IS NULL
        # und loggt Erinnerungen nach 24h / Eskalationen nach 48h.
        self.scheduler.add_job(
            job_briefing_approval_reminders,
            "interval",
            hours=1,
            id="briefing_approval_reminders",
            replace_existing=True,
        )
        logger.info("✓ Daily jobs registered (incl. weekly HWK scraper + token cleanup + briefing reminders)")

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
