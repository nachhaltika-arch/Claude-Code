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
from database import SessionLocal, Project, Communication, DATABASE_URL
from services.margin_calculator import MarginCalculator
from services.base_urls import public_base_url
from services.email import send_email as _send_email_canonical
from services import versandsperre
from automations.email_templates import render_template
from automations.erinnerungen import (
    BRIEFING_STUFEN,
    MATERIAL_STUFEN,
    faellige_erinnerung,
)
from automations.scheduler_kontakt import _send_phase_email, job_check_missing_materials, job_check_overdue_phases, job_phase_postgolive_transitions, job_send_briefing_reminders, job_tag_14_funktionscheck, job_tag_21_bewertungsanfrage, job_tag_30_geo_check, job_tag_30_upsell, job_tag_5_followup
from automations.scheduler_ueberwachung import job_check_all_domains, job_check_netlify_dns, job_check_netlify_ssl
from automations.job_eigene_zertifikate import job_eigene_zertifikate_pruefen
from automations.job_ki_sichtbarkeit import job_ki_sichtbarkeit_woechentlich
from automations.scheduler_bericht import job_monthly_performance_report
from automations.versandmodus import setze_probemodus
import logging
import os

logger = logging.getLogger(__name__)

# Module-level config read once at import


# ===================================================================
# STANDALONE JOB FUNCTIONS (no class instance references)
# ===================================================================





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











def job_anrechnung_ablaufwarnung():
    """Erinnert an Anrechnungen, die in dreissig Tagen verfallen (ORDERS_08).

    **Ein Verkaufsinstrument, kein Serviceschreiben** — und ein zulaessiges:
    Der Empfaenger hat gekauft, die Anrechnung ist ihm zugesagt, der Anlass
    ist sachlich. Genau dafuer wurde sie konstruiert.

    Der Dienst oeffnet seine eigene Sitzung und schliesst sie, **bevor** Brevo
    gerufen wird; siehe `services/anrechnung.ablaufwarnung`.
    """
    from services.anrechnung import ablaufwarnung

    gesendet = ablaufwarnung()
    if gesendet:
        logger.info(f"Anrechnung: {gesendet} Ablaufwarnungen versendet")
    return gesendet


def job_fehlerprotokoll_aufraeumen():
    """Raeumt Eintraege weg, die dreissig Tage lang nicht mehr auftraten."""
    from services.fehlerprotokoll import alte_aufraeumen

    entfernt = alte_aufraeumen()
    if entfernt:
        logger.info(f"Fehlerprotokoll: {entfernt} alte Eintraege entfernt")
    return entfernt








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















# ===================================================================
# MONTHLY PERFORMANCE REPORT
# ===================================================================

def _run_quartals_reaudit():
    """Termingeber fuer das Quartals-Re-Audit der Pflege-Abos (L-101)."""
    try:
        from services.quartals_reaudit import lauf_mit_eigener_sitzung
        lauf_mit_eigener_sitzung()
    except Exception as e:                              # noqa: BLE001
        logger.error(f"Quartals-Re-Audit Wrapper Fehler: {e}", exc_info=True)


def _run_geo_monitoring_sync():
    """Synchroner Wrapper fuer den asynchronen GEO-Monitor-Job."""
    import asyncio
    try:
        from services.geo_monitor import run_monthly_geo_check
        asyncio.run(run_monthly_geo_check())
    except Exception as e:
        logger.error(f"GEO Monitoring Wrapper Fehler: {e}", exc_info=True)












# ===================================================================
# SCHEDULER CLASS (thin wrapper, no job logic)
# ===================================================================

class CompagnonScheduler:
    """APScheduler wrapper for KOMPAGNON automation."""

    def __init__(self, database_url: str = None, use_mock_email: bool = None):
        database_url = database_url or DATABASE_URL
        # Der Schalter liegt seit dem 22.08.2026 in `versandmodus` (L-25):
        # Beim Aufteilen der Datei haette ein Namensimport ihn im
        # Kontakt-Teil eingefroren — der Probemodus waere angezeigt und die
        # Mails trotzdem hinausgegangen.
        #
        # **`None` statt `False` seit dem 24.08.2026 (L-104).** Der
        # Vorgabewert war `False`, und `start_scheduler()` uebergibt nichts —
        # also setzte jeder Start den Probemodus auf „echt versenden"
        # zurueck, **auch wenn `USE_MOCK_EMAIL=true` in der Umgebung stand**.
        # Es gab damit keinen wirksamen Probemodus fuer einen laufenden
        # Dienst; nachgestellt, nicht vermutet.
        #
        # Dieselbe Falle wie oben, eine Ebene hoeher: Dort fror ein kopierter
        # **Name** den Wert ein, hier ueberschrieb ihn ein **Vorgabewert**.
        # `None` heisst jetzt „nimm, was die Umgebung sagt"; wer es
        # ausdruecklich angibt, bestimmt weiterhin.
        if use_mock_email is not None:
            setze_probemodus(use_mock_email)

        # JobStore mit Fallback auf MemoryJobStore wenn DB nicht erreichbar.
        # `SCHEDULER_JOBSTORE=memory` erzwingt den fluechtigen Speicher — ein
        # Test darf die geteilte Jobtabelle nicht anfassen.
        try:
            if os.getenv("SCHEDULER_JOBSTORE", "").strip().lower() == "memory":
                raise RuntimeError("ausdruecklich im Speicher gewuenscht")
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
        registrierte = self._registrieren_und_merken()
        self._verwaiste_wegraeumen(registrierte)
        logger.info("✓ Scheduler started with all daily jobs")

    def _registrieren_und_merken(self) -> set:
        """`_register_daily_jobs` fahren und dabei mitschreiben, was sie anlegt.

        **Warum mitschreiben statt eine Liste pflegen.** Eine Konstante mit den
        festen Kennungen waere klarer zu lesen — und sie waere genau die
        Fehlerquelle, die hier zu schliessen ist: Sie laeuft mit der
        Registrierung auseinander, sobald jemand einen Job umbenennt, und dann
        raeumt der Abgleich den falschen weg. Was tatsaechlich angelegt wurde,
        weiss nur der Aufruf selbst.
        """
        angelegt = set()
        echtes_add_job = self.scheduler.add_job

        def mitschreibend(*args, **kwargs):
            job = echtes_add_job(*args, **kwargs)
            angelegt.add(job.id)
            return job

        self.scheduler.add_job = mitschreibend
        try:
            self._register_daily_jobs()
        finally:
            self.scheduler.add_job = echtes_add_job

        return angelegt

    def _verwaiste_wegraeumen(self, registrierte: set) -> None:
        """Jobs entfernen, die der heutige Code nicht mehr anlegt.

        Sie kommen aus dem **dauerhaften** Jobstore und laufen weiter, obwohl
        sie niemand mehr registriert — produktiv am 23.08.2026 gefunden:
        `netlify_dns_check_every_10min` neben `..._15min`, alle zehn Minuten,
        seit einer Umbenennung. Jeder Fall wird **benannt**, nicht still
        entfernt: Ein lautlos verschwundener Job ist so schwer zu finden wie
        ein lautlos laufender.
        """
        vorhandene = [job.id for job in self.scheduler.get_jobs()]
        for kennung in verwaiste_jobs(vorhandene, registrierte):
            logger.warning(
                "🧹 Job %s stand im Speicher, wird vom Code aber nicht mehr "
                "angelegt — entfernt", kennung,
            )
            self.scheduler.remove_job(kennung)

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("✓ Scheduler stopped")

    def _register_daily_jobs(self):
        """Register cron jobs using standalone functions."""
        # Das Fehlerprotokoll waechst sonst ohne Ende. Was dreissig Tage lang
        # nicht mehr aufgetreten ist, hat niemanden mehr interessiert.
        self.scheduler.add_job(
            job_fehlerprotokoll_aufraeumen,
            "cron",
            hour=4, minute=30,
            id="fehlerprotokoll_aufraeumen",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        # Taeglich frueh, vor dem Arbeitstag: Wer die Mail morgens liest,
        # kann noch am selben Tag anrufen. Der Dienst meldet nur Fristen, die
        # **genau** in dreissig Tagen enden — sonst bekaeme derselbe Kaeufer
        # die Erinnerung an dreissig Tagen hintereinander (ORDERS_08).
        self.scheduler.add_job(
            job_anrechnung_ablaufwarnung,
            "cron",
            hour=7, minute=15,
            id="anrechnung_ablaufwarnung",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        # **Wöchentlich, montags früh.** Jede Frage kostet Geld; der Takt
        # ergibt eine Kurve statt Rauschen. Läuft nur für zahlende Abonnenten
        # und nur, wenn ein Schlüssel hinterlegt ist (L-58 b).
        self.scheduler.add_job(
            job_ki_sichtbarkeit_woechentlich,
            "cron",
            day_of_week="mon", hour=6, minute=0,
            id="ki_sichtbarkeit_woechentlich",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        self.scheduler.add_job(
            job_check_all_domains,
            "interval", hours=6,
            id="domain_check_every_6h",
            replace_existing=True,
        )
        self.scheduler.add_job(
            job_check_netlify_dns,
            "interval", minutes=15,
            id="netlify_dns_check_every_15min",
            replace_existing=True,
        )
        # **Kriterium S1 gilt für uns selbst (B1.14e).** Die Überwachung
        # daneben liest `projects` — unsere eigenen Adressen stehen dort nicht.
        # Eine davon steht gedruckt im Buch.
        self.scheduler.add_job(
            job_eigene_zertifikate_pruefen,
            "cron",
            hour=7, minute=30,
            id="eigene_zertifikate",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        self.scheduler.add_job(
            job_check_netlify_ssl,
            "cron",
            hour=8, minute=0,
            id="netlify_ssl_check",
            replace_existing=True,
            timezone="Europe/Berlin",
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
        # Bug #5: Briefing-Reminder fuer phase_1-Projekte ohne has_briefing.
        # Eskalation Tag 3 / 7 / 14, idempotent ueber Communication.template_key.
        self.scheduler.add_job(
            job_send_briefing_reminders,
            "cron",
            hour=9, minute=30,
            id="daily_send_briefing_reminders",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        # Bug #4: Auto-Transitions phase_6 -> phase_7 (7d) und phase_7 -> completed (30d).
        # phase_5 -> phase_6 wird direkt im DNS-Polling-Job ausgeloest (sobald Site live).
        self.scheduler.add_job(
            job_phase_postgolive_transitions,
            "cron",
            hour=11, minute=0,
            id="daily_phase_postgolive_transitions",
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
        logger.info("✓ Daily jobs registered (incl. weekly HWK scraper)")

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

        # Monatlicher Performance-Report — 1. des Monats, 08:30 Uhr
        self.scheduler.add_job(
            job_monthly_performance_report,
            "cron",
            day=1,
            hour=8,
            minute=30,
            id="monthly_performance_report",
            replace_existing=True,
            timezone="Europe/Berlin",
        )
        logger.info("✓ Monatlicher Performance-Report Job registriert (1. des Monats, 08:30)")

        # GEO Monitoring — 1. des Monats, 07:00 Uhr
        self.scheduler.add_job(
            _run_geo_monitoring_sync,
            "cron",
            day=1,
            hour=7,
            minute=0,
            id="geo_monthly_monitoring",
            replace_existing=True,
            timezone="Europe/Berlin",
            name="Monatlicher GEO-Sichtbarkeits-Check",
        )
        logger.info("✓ Monatlicher GEO-Monitoring Job registriert (1. des Monats, 07:00)")

        # Quartals-Re-Audit der Pflege-Abos — 1. Januar/April/Juli/Oktober,
        # 06:00 Uhr (L-101). **Vor den Monatsjobs um 07:00 und 08:30**, damit
        # die Faelligkeitsmeldung oben in der Glocke steht und nicht unter dem
        # GEO-Bericht.
        #
        # Er stellt nur fest, wer dran ist, und meldet es. Die Pruefung selbst
        # loest ein Mensch aus — sie kostet Guthaben, und die Entscheidung bei
        # einem gefallenen Wert (G4: Nachbesserung ohne Berechnung) gehoert
        # nicht in einen Cron-Eintrag.
        self.scheduler.add_job(
            _run_quartals_reaudit,
            "cron",
            month="1,4,7,10",
            day=1,
            hour=6,
            minute=0,
            id="quartals_reaudit",
            replace_existing=True,
            timezone="Europe/Berlin",
            name="Quartals-Re-Audit der Pflege-Abos",
        )
        logger.info("✓ Quartals-Re-Audit Job registriert (1.1./1.4./1.7./1.10., 06:00)")

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

# Jobs, die **zur Laufzeit** entstehen — je Projekt einer, angelegt beim
# Go-Live. Sie stehen in keiner Registrierungsliste und duerfen deshalb beim
# Aufraeumen nicht mitgehen: Wer hier pauschal loescht, wirft Kundentermine weg.
LAUFZEIT_PRAEFIXE = ("golive_",)

# Werte, die als „aus" gelten. Alles andere laeuft — auch ein Tippfehler.
# **Die sichere Richtung:** Ein Scheduler, der faelschlich laeuft, faellt auf.
# Einer, der faelschlich stillsteht, faellt erst auf, wenn eine Nachfassmail
# ausbleibt, und dann ist der Kunde schon weg.
_AUS = {"false", "0", "no", "nein", "off", "aus"}


def scheduler_ist_eingeschaltet() -> bool:
    """Darf dieser Dienst einen Scheduler fahren?

    **Warum es diesen Schalter gibt (2026-08-23, beim Umzug L-34).** Waehrend
    des Umzugs laufen zwei Produktiv-Dienste gegen **dieselbe** Datenbank —
    Oregon traegt den Verkehr, Frankfurt steht daneben. Beide starteten einen
    Scheduler, und beide hingen ihn an denselben `SQLAlchemyJobStore`.
    APScheduler kennt keine Sperre ueber Prozessgrenzen: Ein faelliger Job
    kann damit zweimal laufen, und unter den vierzehn ist
    `email_sequence_runner`.

    Der Dienst ohne Verkehr setzt `SCHEDULER_ENABLED=false` und ist damit
    still, ohne abgeschaltet zu sein — er bleibt pruefbar.
    """
    return os.getenv("SCHEDULER_ENABLED", "true").strip().lower() not in _AUS


def verwaiste_jobs(vorhandene_ids, registrierte_ids) -> list:
    """Job-Kennungen im Speicher, die der heutige Code nicht mehr anlegt.

    **Der Fund vom 2026-08-23:** Der Jobstore ist dauerhaft, die Registrierung
    nicht. Produktiv stand `netlify_dns_check_every_10min` in der Tabelle und
    lief alle zehn Minuten, obwohl der Code seit einer Umbenennung **nur noch**
    `netlify_dns_check_every_15min` anlegt. Niemand sah es: Im Dashboard steht
    kein Jobstore, und `/api/scheduler/status` zeigt genau das, was in der
    Tabelle steht — also auch den Vorgaenger.

    Laufzeit-Jobs bleiben unberuehrt, siehe `LAUFZEIT_PRAEFIXE`.
    """
    return [
        kennung for kennung in vorhandene_ids
        if kennung not in registrierte_ids
        and not kennung.startswith(LAUFZEIT_PRAEFIXE)
    ]


def get_scheduler(database_url: str = None, use_mock_email: bool = None):
    """Get or create scheduler instance.

    `use_mock_email=None` heisst „nimm, was `USE_MOCK_EMAIL` sagt" (L-104).
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = CompagnonScheduler(database_url, use_mock_email)
    return _scheduler


def start_scheduler():
    """Start the global scheduler. Fehler werden nur geloggt."""
    global _scheduler
    if not scheduler_ist_eingeschaltet():
        logger.info(
            "⏸ Scheduler abgeschaltet (SCHEDULER_ENABLED) — dieser Dienst "
            "faehrt keine Hintergrundjobs. Gewollt, solange ein zweiter "
            "Dienst auf derselben Datenbank sie faehrt."
        )
        return
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
