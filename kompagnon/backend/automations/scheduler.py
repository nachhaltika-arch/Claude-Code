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


def job_content_approval_reminders():
    """Stuendlicher Job: prueft Content-Approvals, die seit 48h+ ausstehen.

    Analog zu job_briefing_approval_reminders (Tor 1), aber fuer Tor 2:
    der Kunde hat eine Freigabe-Anfrage erhalten (content_approval_sent_at
    gesetzt), aber noch nicht freigegeben (content_approved_at NULL).

    - 48h <= Wartezeit < 49h: Erinnerungs-Mail an den Kunden mit dem
      Approval-Link (genau einmal — 1h-Fenster bei stuendlichem Job).
    - >= 72h:                 Eskalations-Log-Eintrag + Admin-Info per Mail.

    Nur Kunden-Reminder werden in diesem Commit tatsaechlich versendet;
    die Admin-Eskalation bleibt vorerst nur Log, weil Eskalations-Mail-
    Empfaenger noch nicht konfiguriert sind (gleicher Punkt wie bei
    briefing_approval_reminders).
    """
    import os
    from sqlalchemy import text as _text
    db = SessionLocal()
    try:
        pending = db.execute(_text("""
            SELECT p.id AS project_id,
                   p.lead_id AS lead_id,
                   p.content_approval_sent_at AS sent_at,
                   p.content_approval_token AS token,
                   COALESCE(l.company_name, l.display_name, '') AS company,
                   COALESCE(l.contact_name, l.display_name, '') AS contact_name,
                   COALESCE(l.email, '') AS email
            FROM projects p
            LEFT JOIN leads l ON l.id = p.lead_id
            WHERE p.content_approval_sent_at IS NOT NULL
              AND p.content_approved_at IS NULL
        """)).fetchall()

        if not pending:
            return

        now = datetime.utcnow()
        reminders_sent = 0
        escalations_sent = 0

        # Kanonische send_email aus services/email.py — keine Klasse mehr
        from services.email import send_email as _canonical_send

        frontend_url = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")

        for row in pending:
            sent_at = row.sent_at
            if not sent_at:
                continue
            hours_waiting = (now - sent_at).total_seconds() / 3600.0

            if 48 <= hours_waiting < 49:
                reminders_sent += 1
                logger.warning(
                    f"⏰ Content-Approval-Reminder: Projekt {row.project_id} "
                    f"({row.company or 'unbekannt'}) wartet seit "
                    f"{int(hours_waiting)}h auf Kundenfreigabe."
                )
                if row.email and row.token:
                    try:
                        approval_url = f"{frontend_url}/approve-content/{row.token}"
                        rendered = render_template("content_approval_reminder", {
                            "company_name": row.company or f"Lead #{row.lead_id or '?'}",
                            "contact_name": row.contact_name or "liebe Kundin / lieber Kunde",
                            "approval_url": approval_url,
                        })
                        body_text = rendered["body"]
                        html_body = (
                            "<pre style=\"font-family:-apple-system,sans-serif;"
                            "font-size:14px;white-space:pre-wrap\">"
                            + body_text + "</pre>"
                        )
                        ok = _canonical_send(
                            to_email=row.email,
                            subject=rendered["subject"],
                            html_body=html_body,
                            text_body=body_text,
                        )
                        if ok:
                            logger.info(
                                f"content_approval_reminders: Reminder an {row.email} (Projekt {row.project_id})"
                            )
                        else:
                            logger.warning(
                                f"content_approval_reminders: Reminder an {row.email} "
                                f"fehlgeschlagen (Projekt {row.project_id}) — SMTP pruefen."
                            )
                    except Exception as e:
                        logger.error(
                            f"content_approval_reminders: Reminder an {row.email} fehlgeschlagen: {e}"
                        )

            elif hours_waiting >= 72:
                escalations_sent += 1
                logger.error(
                    f"🚨 ESKALATION: Content-Approval fuer Projekt {row.project_id} "
                    f"({row.company or 'unbekannt'}) wartet seit "
                    f"{int(hours_waiting)}h auf Kundenfreigabe!"
                )
                # TODO: Eskalations-Mail an Admin wie bei briefing_approval_reminders.

        if reminders_sent or escalations_sent:
            logger.info(
                f"content_approval_reminders: {reminders_sent} Reminder, "
                f"{escalations_sent} Eskalationen (total pending: {len(pending)})"
            )
    except Exception as e:
        logger.error(f"content_approval_reminders Job Fehler: {e}")
    finally:
        db.close()


# ── Hebel #5: Monatlicher Performance-Report ──────────────────────────────────
#
# Cron-Job am 1. jeden Monats um 08:30 Berlin-Zeit. Pro aktivem Kunden:
#   1. Frische PageSpeed-Messung via Google PageSpeed API
#   2. Vergleich mit perf_report_last_mobile (Score vom letzten Report)
#   3. KI-Kommentar via Claude (mit Fallback-Text wenn ANTHROPIC_API_KEY fehlt)
#   4. HTML-E-Mail mit Score-Karten + Trend + KI-Analyse + ggf. Upsell-Box
#   5. send_email via kanonischer services.email
#   6. perf_report_*-Tracking-Spalten auf dem Lead aktualisieren


def _measure_pagespeed_sync(url: str, api_key: str):
    """Synchroner PageSpeed-Call fuer Mobile + Desktop.

    APScheduler-Jobs laufen in einem ThreadPool — kein Event-Loop, deshalb
    sync httpx statt async/await. Returnt (mobile_score, desktop_score) als
    Tupel von ints (0-100) oder None bei Fehlern. Eigene Errors werden NICHT
    geworfen — der aufrufende Job entscheidet, ob er den fehlenden Score
    toleriert.
    """
    import httpx as _httpx
    results = []
    for strategy in ("mobile", "desktop"):
        try:
            resp = _httpx.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params={
                    "url": url,
                    "key": api_key,
                    "strategy": strategy,
                    "category": "performance",
                },
                timeout=30.0,
            )
            if resp.is_success:
                data = resp.json()
                score = (
                    data.get("lighthouseResult", {})
                        .get("categories", {})
                        .get("performance", {})
                        .get("score")
                )
                results.append(int(score * 100) if score is not None else None)
            else:
                results.append(None)
        except Exception:
            results.append(None)
    return results[0], results[1]  # (mobile, desktop)


def _fallback_perf_comment(mobile, diff) -> str:
    """Fallback-Text wenn ANTHROPIC_API_KEY fehlt oder Claude nicht erreichbar."""
    score = mobile if mobile is not None else 0
    if score >= 85:
        return (
            "Ihre Website performt ausgezeichnet. Der hohe Score sorgt fuer "
            "bessere Google-Rankings und schnellere Ladezeiten fuer Ihre Besucher."
        )
    if score >= 70:
        return (
            "Ihre Website laeuft gut. Mit einigen Optimierungen — etwa "
            "Bildkomprimierung — laesst sich der Score noch weiter verbessern."
        )
    return (
        "Ihre Website hat Optimierungsbedarf. Ein niedriger PageSpeed-Score "
        "kann sich negativ auf Google-Rankings und Absprungrate auswirken."
    )


def _generate_perf_comment(
    company: str, url: str,
    mobile, desktop,
    last_mobile, diff,
) -> str:
    """Generiert einen kurzen KI-Kommentar (2-3 Saetze) zum Monatsreport.

    Bei Claude-API-Fehler (Netzwerk, Auth, JSON, Timeout) faellt es auf den
    statischen _fallback_perf_comment zurueck. Fehler werden nur auf Debug-
    Level geloggt, weil ein fehlender KI-Kommentar kein Hard-Fail ist.
    """
    import os as _os
    import httpx as _httpx

    api_key = _os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_perf_comment(mobile, diff)

    if diff is None:
        trend_text = "erste Messung — kein Vergleich verfuegbar"
    elif diff > 2:
        trend_text = f"verbessert um {diff} Punkte gegenueber Vormonat"
    elif diff < -2:
        trend_text = f"verschlechtert um {abs(diff)} Punkte gegenueber Vormonat"
    else:
        trend_text = "stabil geblieben (kleine Schwankung)"

    prompt = (
        f"Schreibe 2-3 Saetze als freundlicher Website-Berater fuer einen Monatsbericht.\n"
        f"Firma: {company} | Website: {url}\n"
        f"PageSpeed Mobil: {mobile}/100 | Desktop: {desktop if desktop is not None else '—'}/100\n"
        f"Trend: {trend_text}\n\n"
        f"Ton: professionell, kurz, konkret. Ein positiver Aspekt, ein Verbesserungshinweis. "
        f"Max 60 Woerter. Kein HTML. Nur der Text."
    )

    try:
        resp = _httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20.0,
        )
        if resp.is_success:
            text_block = resp.json().get("content", [{}])[0].get("text", "").strip()
            if text_block:
                return text_block
    except Exception as e:
        logger.debug(f"_generate_perf_comment Claude-Fallback ({e})")

    return _fallback_perf_comment(mobile, diff)


def _build_perf_report_email(
    company, website_url,
    mobile, desktop,
    last_mobile, mobile_diff,
    ki_kommentar, upsell, report_count,
) -> str:
    """Baut die HTML-Report-E-Mail."""
    month = datetime.utcnow().strftime("%B %Y")

    score_color = (
        "#059669" if (mobile or 0) >= 85
        else "#D97706" if (mobile or 0) >= 70
        else "#DC2626"
    )
    score_label = (
        "Sehr gut" if (mobile or 0) >= 85
        else "Gut" if (mobile or 0) >= 70
        else "Optimierungsbedarf"
    )

    if mobile_diff is None:
        trend_html = '<span style="color:#6B7280;">Erste Messung — kein Vergleich verfuegbar</span>'
    elif mobile_diff > 2:
        trend_html = (
            f'<span style="color:#059669;font-weight:700;">'
            f'\u25B2 +{mobile_diff} Punkte gegenueber Vormonat</span>'
        )
    elif mobile_diff < -2:
        trend_html = (
            f'<span style="color:#DC2626;font-weight:700;">'
            f'\u25BC {mobile_diff} Punkte gegenueber Vormonat</span>'
        )
    else:
        trend_html = (
            f'<span style="color:#6B7280;">'
            f'\u25B6 Stabil (\u00B1{abs(mobile_diff)} Punkte)</span>'
        )

    upsell_html = ""
    if upsell:
        upsell_html = """
        <div style="background:#FEF3C7;border-left:4px solid #D97706;
                    padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;">
          <div style="font-weight:700;color:#92400E;margin-bottom:6px;">
            \U0001F4A1 Empfehlung: Website-Optimierung
          </div>
          <div style="font-size:13px;color:#92400E;line-height:1.6;">
            Ein Score unter 70 kostet Sie taeglich potenzielle Kunden.
            Mit unserem <strong>Performance-Paket</strong> optimieren wir
            Ladezeiten, Bilder und technische Faktoren gezielt.<br><br>
            <a href="mailto:info@kompagnon.de"
               style="color:#92400E;font-weight:700;">
              Jetzt kostenloses Beratungsgespraech anfragen \u2192
            </a>
          </div>
        </div>
        """

    desktop_display = desktop if desktop is not None else "\u2013"

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#1a2332;">
      <div style="background:#008EAA;padding:20px 24px;border-radius:8px 8px 0 0;">
        <div style="color:#fff;font-size:18px;font-weight:700;">KOMPAGNON</div>
        <div style="color:rgba(255,255,255,.75);font-size:13px;">
          Ihr monatlicher Website-Report — {month}
        </div>
      </div>
      <div style="padding:24px;background:#fff;border:1px solid #e2e8f0;
                  border-top:none;border-radius:0 0 8px 8px;">

        <p style="margin:0 0 20px;font-size:15px;">
          Guten Tag, <strong>{company}</strong>,
        </p>

        <table cellpadding="0" cellspacing="0" border="0"
               style="width:100%;margin-bottom:20px;border-collapse:separate;border-spacing:8px 0;">
          <tr>
            <td style="width:50%;text-align:center;padding:16px;
                       background:#f8fafc;border-radius:8px;
                       border:2px solid {score_color};">
              <div style="font-size:11px;color:#6B7280;
                          text-transform:uppercase;margin-bottom:4px;">Mobil</div>
              <div style="font-size:36px;font-weight:800;color:{score_color};">{mobile}</div>
              <div style="font-size:12px;color:{score_color};font-weight:600;">{score_label}</div>
            </td>
            <td style="width:50%;text-align:center;padding:16px;
                       background:#f8fafc;border-radius:8px;">
              <div style="font-size:11px;color:#6B7280;
                          text-transform:uppercase;margin-bottom:4px;">Desktop</div>
              <div style="font-size:36px;font-weight:800;color:#374151;">{desktop_display}</div>
              <div style="font-size:12px;color:#6B7280;">Score /100</div>
            </td>
          </tr>
        </table>

        <div style="margin-bottom:16px;font-size:13px;">{trend_html}</div>

        <div style="background:#F0F9FF;border-radius:8px;padding:14px 16px;margin-bottom:20px;">
          <div style="font-size:12px;font-weight:700;color:#0369A1;margin-bottom:6px;">
            \U0001F4CA KI-Analyse
          </div>
          <div style="font-size:13px;color:#374151;line-height:1.7;">
            {ki_kommentar}
          </div>
        </div>

        {upsell_html}

        <div style="font-size:12px;color:#6B7280;margin-top:20px;">
          <a href="{website_url}" style="color:#008EAA;">{website_url}</a>
          &middot; Report #{report_count} &middot; Gemessen am {month}
        </div>

        <div style="margin-top:20px;padding-top:20px;border-top:1px solid #e2e8f0;
                    font-size:12px;color:#6B7280;">
          <strong>KOMPAGNON Communications</strong><br>
          Bei Fragen: <a href="mailto:info@kompagnon.de" style="color:#008EAA;">info@kompagnon.de</a>
        </div>
      </div>
    </div>
    """


def job_monthly_performance_report():
    """Monatlicher Performance-Report-Job — APScheduler cron, 1. des Monats 08:30 Berlin.

    Fuer jeden aktiven Lead (mit E-Mail, Website, Go-Live oder aktiver
    Netlify-Domain): PageSpeed messen → mit Vormonat vergleichen →
    KI-Kommentar generieren → HTML-E-Mail senden → Tracking-Spalten updaten.

    Einzelne Lead-Fehler werden geloggt, brechen aber nicht den ganzen Job ab.
    """
    import os as _os
    from sqlalchemy import text as _text
    from services.email import send_email

    logger.info("\U0001F4CA Monatlicher Performance-Report gestartet...")

    db = SessionLocal()
    try:
        leads = db.execute(_text("""
            SELECT
                l.id,
                l.email,
                l.company_name,
                l.website_url,
                l.pagespeed_mobile_score,
                l.pagespeed_desktop_score,
                l.pagespeed_checked_at,
                l.perf_report_last_mobile,
                l.perf_report_last_desktop,
                l.perf_report_sent_count
            FROM leads l
            WHERE l.email IS NOT NULL
              AND l.email != ''
              AND l.website_url IS NOT NULL
              AND l.website_url != ''
              AND (
                  l.actual_go_live IS NOT NULL
                  OR EXISTS (
                      SELECT 1 FROM projects p
                      WHERE p.lead_id = l.id
                        AND p.netlify_domain_status = 'active'
                  )
              )
        """)).fetchall()

        logger.info(f"Performance-Report: {len(leads)} aktive Kunden gefunden")

        api_key = _os.getenv("PAGESPEED_API_KEY", "")
        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for row in leads:
            lead_id         = row[0]
            email           = row[1]
            company         = row[2] or "Ihr Unternehmen"
            website_url     = row[3]
            current_mobile  = row[4]
            current_desktop = row[5]
            last_mobile     = row[7]   # Vormonat-Score (perf_report_last_mobile)
            report_count    = row[9] or 0

            try:
                # 1. Frische PageSpeed-Messung — Fallback auf gespeicherte Werte
                new_mobile, new_desktop = current_mobile, current_desktop
                if api_key and website_url:
                    try:
                        m, d = _measure_pagespeed_sync(website_url, api_key)
                        # Nur uebernehmen wenn die Messung tatsaechlich was lieferte
                        if m is not None:
                            new_mobile = m
                        if d is not None:
                            new_desktop = d
                    except Exception as ps_err:
                        logger.warning(
                            f"PageSpeed-Messung fehlgeschlagen fuer Lead {lead_id}: {ps_err}"
                        )

                if new_mobile is None:
                    logger.info(
                        f"Ueberspringe Lead {lead_id} ({email}) — kein PageSpeed-Score"
                    )
                    skipped_count += 1
                    continue

                # 2. Trend-Differenz
                mobile_diff = None
                if last_mobile is not None and new_mobile is not None:
                    mobile_diff = new_mobile - last_mobile

                # 3. KI-Kommentar
                ki_kommentar = _generate_perf_comment(
                    company, website_url, new_mobile, new_desktop,
                    last_mobile, mobile_diff,
                )

                # 4. Upsell-Flag (Score < 70 → Optimierungs-Box)
                upsell = new_mobile < 70

                # 5. HTML-Body
                html_body = _build_perf_report_email(
                    company=company,
                    website_url=website_url,
                    mobile=new_mobile,
                    desktop=new_desktop,
                    last_mobile=last_mobile,
                    mobile_diff=mobile_diff,
                    ki_kommentar=ki_kommentar,
                    upsell=upsell,
                    report_count=report_count + 1,
                )

                # 6. Betreff mit Trend-Emoji
                trend_emoji = (
                    "\U0001F4C8" if (mobile_diff or 0) > 2          # 📈
                    else "\U0001F4C9" if (mobile_diff or 0) < -2    # 📉
                    else "\U0001F4CA"                                # 📊
                )
                month = datetime.utcnow().strftime("%B %Y")
                subject = f"{trend_emoji} Ihr Website-Report {month} — Score: {new_mobile}/100"

                # 7. Versand via kanonische send_email
                ok = send_email(
                    to_email=email,
                    subject=subject,
                    html_body=html_body,
                )

                if ok:
                    # 8. Tracking-Spalten aktualisieren — der "neue Score" wird zum
                    #    Vergleichswert fuer den naechsten Monat. Idempotent durch
                    #    COALESCE — falls Migration v10 noch nicht in DB ist, schlaegt
                    #    der ALTER nicht den Job ab, sondern wird im except gefangen.
                    try:
                        db.execute(_text("""
                            UPDATE leads SET
                                pagespeed_mobile_score   = :mobile,
                                pagespeed_desktop_score  = :desktop,
                                pagespeed_checked_at     = NOW(),
                                perf_report_last_mobile  = :mobile,
                                perf_report_last_desktop = :desktop,
                                perf_report_sent_at      = NOW(),
                                perf_report_sent_count   = COALESCE(perf_report_sent_count, 0) + 1
                            WHERE id = :lid
                        """), {
                            "mobile":  new_mobile,
                            "desktop": new_desktop,
                            "lid":     lead_id,
                        })
                        db.commit()
                    except Exception as upd_err:
                        logger.warning(
                            f"Performance-Report: Tracking-Update fuer Lead {lead_id} "
                            f"fehlgeschlagen ({upd_err}) — Mail wurde trotzdem gesendet."
                        )
                        try:
                            db.rollback()
                        except Exception:
                            pass
                    sent_count += 1
                    logger.info(
                        f"\u2713 Performance-Report gesendet: Lead {lead_id} "
                        f"({email}) Score: {new_mobile}/100"
                    )
                else:
                    failed_count += 1
                    logger.warning(
                        f"Performance-Report: send_email an {email} fehlgeschlagen "
                        f"(Lead {lead_id}) — SMTP-Konfiguration pruefen."
                    )

            except Exception as lead_err:
                failed_count += 1
                logger.warning(
                    f"Performance-Report Lead {lead_id} Fehler: {lead_err}"
                )
                continue

        logger.info(
            f"\u2713 Performance-Report abgeschlossen: "
            f"{sent_count} gesendet, {skipped_count} uebersprungen, "
            f"{failed_count} fehlgeschlagen, {len(leads)} Leads gesamt"
        )

    except Exception as e:
        logger.error(f"Performance-Report Job-Fehler: {e}", exc_info=True)
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
        # Stuendlicher Content-Approval-Reminder — Tor 2 der
        # Funnel-Automation. Prueft projects mit
        # content_approval_sent_at IS NOT NULL AND content_approved_at IS NULL
        # und sendet Kunden-Erinnerungen nach 48h, Eskalationen nach 72h.
        self.scheduler.add_job(
            job_content_approval_reminders,
            "interval",
            hours=1,
            id="content_approval_reminders",
            replace_existing=True,
        )
        # Hebel #5 — Monatlicher Performance-Report.
        # Cron am 1. jeden Monats um 08:30 Berlin-Zeit. Pro aktiver Kunde:
        # PageSpeed messen, KI-Kommentar generieren, HTML-E-Mail senden.
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
        logger.info(
            "✓ Daily jobs registered (incl. weekly HWK scraper + token cleanup "
            "+ approval reminders + monthly performance report)"
        )

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
