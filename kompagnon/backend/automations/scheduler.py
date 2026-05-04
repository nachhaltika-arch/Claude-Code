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
from services.email import send_email as _send_email_canonical
from automations.email_templates import render_template
import logging
import os

logger = logging.getLogger(__name__)

# Module-level config read once at import
_use_mock_email = os.getenv("USE_MOCK_EMAIL", "false").lower() == "true"


# ===================================================================
# STANDALONE JOB FUNCTIONS (no class instance references)
# ===================================================================

def _do_send_email(to_email: str, subject: str, html_body: str) -> bool:
    if _use_mock_email:
        logger.info(f"[MOCK] E-Mail an {to_email}: {subject}")
        return True
    return _send_email_canonical(to_email=to_email, subject=subject, html_body=html_body)


def _send_phase_email(project_id: int, template_key: str):
    """Send template email for a project (standalone function)."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project or not project.lead:
            return

        lead = project.lead
        frontend_url = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")
        context = {
            "company_name":         lead.company_name or "Ihr Unternehmen",
            "contact_name":         lead.contact_name or "liebe Kundin / lieber Kunde",
            "assigned_person":      "KOMPAGNON-Team",
            "contact_person_phone": os.getenv("CONTACT_PHONE", "+49 (0) 261 88 44 70"),
            "contact_person_email": os.getenv("CONTACT_EMAIL", "info@kompagnon.eu"),
            "preview_link":         f"{frontend_url}/portal",
            "upload_link":          f"{frontend_url}/portal",
            "review_deadline":      (datetime.utcnow() + timedelta(days=5)).strftime("%d.%m.%Y"),
            "kickoff_date":         (datetime.utcnow() + timedelta(days=2)).strftime("%d.%m.%Y"),
            "new_visitors":         "—",
            "form_submissions":     "—",
            "pagespeed_score":      "—",
            "review_link":          "https://g.page/r/kompagnon",
        }

        rendered = render_template(template_key, context)
        success = _do_send_email(
            to_email=lead.email,
            subject=rendered["subject"],
            html_body=rendered["body"],
        )

        if success:
            try:
                comm = Communication(
                    project_id=project_id,
                    type="email",
                    direction="outbound",
                    channel="email",
                    subject=rendered["subject"],
                    body=rendered["body"][:500],
                    is_automated=True,
                    template_key=template_key,
                    sent_at=datetime.utcnow(),
                )
                db.add(comm)
                db.commit()
            except Exception as log_err:
                logger.warning(f"log_communication fehlgeschlagen: {log_err}")
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
    """
    Prüft DNS-Status aller Projekte mit pendingem Custom-Domain-Status.

    Verbesserungen gegenüber der alten Version:
    - Überspringt Projekte im Backoff-Zeitraum (nach Fehler-Häufung)
    - Jitter: zufällige 0–3s Verzögerung verhindert Thundering-Herd
    - Exponential Backoff bei aufeinanderfolgenden Fehlern
    - Per-Projekt-Commit verhindert Datenverlust bei teilweisem Fehler
    """
    import random
    import time as _time
    from sqlalchemy import text as _text
    from datetime import datetime as _dt, timedelta as _td

    try:
        from services.netlify_service import check_dns_active
    except Exception as e:
        logger.warning(f"Netlify DNS-Check: service import fehlgeschlagen: {e}")
        return

    logger.info("DNS-Polling: Start")
    db = SessionLocal()
    now = _dt.utcnow()

    try:
        pending = db.execute(_text("""
            SELECT id, netlify_domain, netlify_site_url, lead_id,
                   COALESCE(netlify_dns_fail_count, 0) AS fail_count,
                   netlify_dns_retry_after
            FROM projects
            WHERE netlify_domain IS NOT NULL
              AND netlify_domain_status = 'pending'
              AND (netlify_dns_retry_after IS NULL OR netlify_dns_retry_after < :now)
              AND (netlify_golive_mail_sent IS NULL OR netlify_golive_mail_sent = false)
            ORDER BY id
            LIMIT 50
        """), {"now": now}).fetchall()

        if not pending:
            logger.info("DNS-Polling: Keine Projekte zu prüfen")
            return

        logger.info(f"DNS-Polling: {len(pending)} Projekte zu prüfen")

        for p in pending:
            # Jitter: 0–3s Verzögerung pro Projekt
            _time.sleep(random.uniform(0, 3))

            project_id   = p[0]
            domain       = p[1]
            site_url     = p[2] or ""
            lead_id      = p[3]
            fail_count   = p[4]

            try:
                is_active = check_dns_active(domain, site_url)

                if is_active:
                    db.execute(_text("""
                        UPDATE projects SET
                          netlify_domain_status   = 'active',
                          netlify_ssl_active      = TRUE,
                          netlify_dns_fail_count  = 0,
                          netlify_dns_retry_after = NULL,
                          updated_at              = NOW()
                        WHERE id = :id
                    """), {"id": project_id})
                    # Portal-Benachrichtigung
                    try:
                        db.execute(_text("""
                            INSERT INTO messages
                              (lead_id, channel, content, direction, created_at, sender_role)
                            VALUES (:lead_id, 'in_app', :content, 'outbound', NOW(), 'system')
                        """), {
                            "lead_id": lead_id,
                            "content": (
                                f"Ihre Website ist jetzt unter {domain} live! "
                                f"Das SSL-Zertifikat wird automatisch innerhalb weniger Minuten aktiviert."
                            ),
                        })
                    except Exception as me:
                        logger.warning(f"DNS-Live-Nachricht Fehler Projekt {project_id}: {me}")

                    # ── Go-Live-E-Mail an Kunden senden ─────────────────────
                    try:
                        lead_row = db.execute(
                            _text("SELECT email, company_name FROM leads WHERE id = :lid"),
                            {"lid": lead_id},
                        ).fetchone()

                        if lead_row and lead_row[0]:
                            customer_email   = lead_row[0]
                            customer_company = lead_row[1] or "Ihr Unternehmen"

                            html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:580px;margin:0 auto;">
  <div style="background:#059669;padding:28px 24px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:40px;margin-bottom:8px;">&#127881;</div>
    <h1 style="color:#fff;font-size:22px;font-weight:700;margin:0;">
      Ihre Website ist jetzt live!
    </h1>
  </div>
  <div style="background:#f8fffe;padding:24px;border:1px solid #d1fae5;border-top:none;border-radius:0 0 12px 12px;">
    <p style="color:#1e3a2f;font-size:15px;line-height:1.6;">
      Hallo {customer_company},
    </p>
    <p style="color:#374151;font-size:14px;line-height:1.7;">
      Ihre neue Website ist ab sofort unter folgender Adresse erreichbar:
    </p>
    <div style="text-align:center;margin:20px 0;">
      <a href="https://{domain}"
         style="display:inline-block;padding:14px 28px;background:#059669;color:#fff;
                border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">
        &#127760; {domain} &#246;ffnen &#8594;
      </a>
    </div>
    <div style="background:#ecfdf5;border-radius:8px;padding:14px 16px;margin:16px 0;">
      <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#065f46;">
        Was als n&#228;chstes passiert:
      </p>
      <ul style="margin:0;padding-left:18px;font-size:13px;color:#374151;line-height:1.8;">
        <li>Das SSL-Zertifikat (Schloss-Symbol) wird in den n&#228;chsten Minuten automatisch aktiviert</li>
        <li>Google indexiert Ihre Seite in den n&#228;chsten Tagen</li>
        <li>Wir melden uns in K&#252;rze f&#252;r einen abschlie&#223;enden Qualit&#228;ts-Check</li>
      </ul>
    </div>
    <p style="color:#374151;font-size:13px;line-height:1.6;">
      Bei Fragen stehen wir Ihnen jederzeit zur Verf&#252;gung.
    </p>
    <p style="color:#374151;font-size:13px;margin-top:20px;">
      Mit freundlichen Gr&#252;&#223;en,<br>
      <strong>Ihr KOMPAGNON-Team</strong>
    </p>
  </div>
</div>"""

                            ok = _do_send_email(
                                to_email=customer_email,
                                subject=f"Ihre Website {domain} ist jetzt live!",
                                html_body=html_body,
                            )
                            if ok:
                                db.execute(
                                    _text("""
                                        UPDATE projects SET
                                          netlify_golive_mail_sent    = true,
                                          netlify_golive_mail_sent_at = NOW()
                                        WHERE id = :id
                                    """),
                                    {"id": project_id},
                                )
                                logger.info(f"✓ Go-Live-Mail gesendet an {customer_email} (Projekt {project_id})")
                            else:
                                logger.warning(
                                    f"Go-Live-Mail an {customer_email} fehlgeschlagen "
                                    f"(Projekt {project_id}) — SMTP prüfen"
                                )
                    except Exception as mail_err:
                        logger.warning(f"Go-Live-Mail Fehler Projekt {project_id}: {mail_err}")

                    logger.info(f"✓ DNS aktiv: {domain} (Projekt {project_id})")
                else:
                    # Nicht aktiv — Fail-Count erhöhen, Backoff setzen
                    new_fail_count  = fail_count + 1
                    backoff_minutes = min(15 * (2 ** fail_count), 1440)  # 15m, 30m, 60m … max 24h
                    retry_after     = now + _td(minutes=backoff_minutes)
                    db.execute(_text("""
                        UPDATE projects
                        SET netlify_dns_fail_count  = :fc,
                            netlify_dns_retry_after = :ra
                        WHERE id = :id
                    """), {"fc": new_fail_count, "ra": retry_after, "id": project_id})
                    logger.info(
                        f"DNS-Polling: {domain} (Projekt {project_id}) — "
                        f"noch nicht aktiv, nächster Versuch in {backoff_minutes}min"
                    )

                db.commit()

            except Exception as pe:
                logger.warning(f"DNS-Check Projekt {project_id} Fehler: {type(pe).__name__}: {pe}")
                try:
                    db.rollback()
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"Netlify DNS-Check unbehandelter Fehler: {e}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()
        logger.info("DNS-Polling: Abgeschlossen")


def job_check_netlify_ssl():
    """
    Prüft täglich ob SSL auf aktiven Netlify-Sites noch gültig ist.
    Netlify erneuert Let's Encrypt automatisch — ABER die Erneuerung
    schlägt fehl wenn DNS falsch konfiguriert oder Domain umgezogen wurde.
    """
    from sqlalchemy import text as _text
    import asyncio

    db = SessionLocal()
    try:
        from services.netlify_service import get_site_status
    except Exception as e:
        logger.warning(f"SSL-Check: service import fehlgeschlagen: {e}")
        db.close()
        return

    try:
        sites = db.execute(_text("""
            SELECT id, netlify_site_id, netlify_domain,
                   netlify_ssl_active, lead_id
            FROM projects
            WHERE netlify_site_id IS NOT NULL
              AND netlify_domain IS NOT NULL
              AND netlify_domain_status = 'active'
        """)).fetchall()

        for site in sites:
            try:
                live = asyncio.run(get_site_status(site[1]))
                ssl_now = bool(live.get("ssl"))

                db.execute(_text("""
                    UPDATE projects
                    SET netlify_ssl_active      = :ssl,
                        netlify_ssl_checked_at  = NOW()
                    WHERE id = :id
                """), {"ssl": ssl_now, "id": site[0]})
                db.commit()

                if site[3] and not ssl_now:
                    logger.warning(
                        f"SSL-Problem: Projekt {site[0]} ({site[2]}) — Zertifikat abgelaufen/fehlt"
                    )
                    _send_ssl_alert(site[0], site[4], site[2], db)

            except Exception as e:
                logger.error(f"SSL-Check Fehler Projekt {site[0]}: {e}")

    finally:
        db.close()


def _send_ssl_alert(project_id: int, lead_id: int, domain: str, db):
    """Sendet SSL-Problem-Alert als Portal-Nachricht + E-Mail an Kunden."""
    from sqlalchemy import text
    try:
        db.execute(text("""
            INSERT INTO messages
              (lead_id, channel, content, direction, created_at, sender_role)
            VALUES
              (:lid, 'in_app', :content, 'outbound', NOW(), 'system')
        """), {
            "lid":     lead_id,
            "content": (
                f"⚠️ SSL-Zertifikat Problem: {domain} hat kein gültiges SSL. "
                f"Mögliche Ursachen: DNS-Konfiguration geändert, Domain umgezogen. "
                f"Bitte im Netlify-Dashboard prüfen und SSL manuell erneuern."
            ),
        })
        db.commit()
        logger.info(f"SSL-Alert Portal-Nachricht gesendet für {domain}")
    except Exception as e:
        logger.warning(f"SSL-Alert Portal-Nachricht Fehler: {e}")

    try:
        lead = db.execute(
            text("SELECT email, company_name FROM leads WHERE id = :id"),
            {"id": lead_id}
        ).fetchone()

        if lead and lead[0]:
            html_body = f"""
            <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
              <div style="background:#FEF2F2;border-left:4px solid #EF4444;
                          padding:16px 20px;border-radius:8px;margin-bottom:16px">
                <p style="font-size:15px;font-weight:600;color:#991B1B;margin:0 0 8px">
                  ⚠️ Sicherheitshinweis für {domain}
                </p>
                <p style="font-size:13px;color:#7F1D1D;margin:0">
                  Das SSL-Zertifikat Ihrer Website <strong>{domain}</strong>
                  konnte nicht automatisch erneuert werden.
                  Besucher sehen derzeit eine Sicherheitswarnung im Browser.
                </p>
              </div>
              <p style="font-size:13px;color:#374151">
                Wir kümmern uns sofort darum und melden uns innerhalb von
                24 Stunden bei Ihnen.
              </p>
              <p style="font-size:13px;color:#374151">
                <strong>Was Sie wissen sollten:</strong><br>
                SSL-Zertifikate schützen die Daten Ihrer Besucher und sind
                für die Google-Platzierung wichtig. Die Erneuerung erfolgt
                normalerweise automatisch — in Ihrem Fall ist ein manueller
                Eingriff nötig.
              </p>
              <div style="background:#F3F4F6;padding:12px 16px;border-radius:6px;
                          font-size:12px;color:#6B7280;margin-top:16px">
                KOMPAGNON Communications · kompagnon.eu
              </div>
            </div>
            """
            from services.email import send_email
            send_email(
                to_email=lead[0],
                subject=f"Wichtig: SSL-Zertifikat für {domain} benötigt Erneuerung",
                html_body=html_body,
            )
            logger.info(f"SSL-Alert E-Mail gesendet an {lead[0]}")
    except Exception as e:
        logger.warning(f"SSL-Alert E-Mail Fehler: {e}")


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


# ===================================================================
# MONTHLY PERFORMANCE REPORT
# ===================================================================

def _run_geo_monitoring_sync():
    """Synchroner Wrapper fuer den asynchronen GEO-Monitor-Job."""
    import asyncio
    try:
        from services.geo_monitor import run_monthly_geo_check
        asyncio.run(run_monthly_geo_check())
    except Exception as e:
        logger.error(f"GEO Monitoring Wrapper Fehler: {e}", exc_info=True)


def job_monthly_performance_report():
    """
    Monatlicher Performance-Report: am 1. jeden Monats für alle aktiven Kunden.
    Misst PageSpeed neu, vergleicht mit Vormonat, sendet E-Mail mit KI-Kommentar.
    """
    from sqlalchemy import text
    from services.email import send_email as _send_report_email

    logger.info("📊 Monatlicher Performance-Report gestartet...")

    db = SessionLocal()
    try:
        leads = db.execute(text("""
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
        sent_count = 0

        for row in leads:
            lead_id         = row[0]
            email           = row[1]
            company         = row[2] or "Ihr Unternehmen"
            website_url     = row[3]
            current_mobile  = row[4]
            current_desktop = row[5]
            last_mobile     = row[7]
            last_desktop    = row[8]
            report_count    = row[9] or 0

            try:
                api_key = os.getenv("PAGESPEED_API_KEY", "")
                new_mobile, new_desktop = current_mobile, current_desktop

                if api_key and website_url:
                    try:
                        new_mobile, new_desktop = _measure_pagespeed_sync(website_url, api_key)
                    except Exception as ps_err:
                        logger.warning(f"PageSpeed-Messung fehlgeschlagen für Lead {lead_id}: {ps_err}")

                if new_mobile is None:
                    logger.info(f"Überspringe Lead {lead_id} — kein PageSpeed-Score")
                    continue

                mobile_diff = (new_mobile - last_mobile) if (last_mobile is not None) else None

                ki_kommentar = _generate_perf_comment(
                    company, website_url, new_mobile, new_desktop or 0, last_mobile, mobile_diff
                )

                upsell = new_mobile < 70

                html_body = _build_report_email(
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

                trend_emoji = (
                    "📈" if (mobile_diff or 0) > 2
                    else "📉" if (mobile_diff or 0) < -2
                    else "📊"
                )
                month = datetime.utcnow().strftime("%B %Y")
                subject = f"{trend_emoji} Ihr Website-Report {month} — Score: {new_mobile}/100"

                ok = _send_report_email(to_email=email, subject=subject, html_body=html_body)

                if ok:
                    db.execute(text("""
                        UPDATE leads SET
                            pagespeed_mobile_score   = :mobile,
                            pagespeed_desktop_score  = :desktop,
                            pagespeed_checked_at     = NOW(),
                            perf_report_last_mobile  = :mobile,
                            perf_report_last_desktop = :desktop,
                            perf_report_sent_at      = NOW(),
                            perf_report_sent_count   = COALESCE(perf_report_sent_count, 0) + 1
                        WHERE id = :lid
                    """), {"mobile": new_mobile, "desktop": new_desktop, "lid": lead_id})
                    sent_count += 1
                    logger.info(
                        f"✓ Performance-Report gesendet: Lead {lead_id} "
                        f"({email}) Score: {new_mobile}/100"
                    )

            except Exception as lead_err:
                logger.warning(f"Performance-Report Lead {lead_id} Fehler: {lead_err}")
                continue

        db.commit()
        logger.info(f"✓ Performance-Report abgeschlossen: {sent_count}/{len(leads)} gesendet")

    except Exception as e:
        logger.error(f"Performance-Report Fehler: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def _measure_pagespeed_sync(url: str, api_key: str):
    """Synchrone PageSpeed-Messung für den Scheduler-Thread."""
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
                score = (data.get("lighthouseResult", {})
                             .get("categories", {})
                             .get("performance", {})
                             .get("score"))
                results.append(int(score * 100) if score is not None else None)
            else:
                results.append(None)
        except Exception:
            results.append(None)
    return results[0], results[1]


def _generate_perf_comment(company, url, mobile, desktop, last_mobile, diff) -> str:
    """Kurzer KI-Kommentar für den Performance-Report. Fällt auf Fallback zurück."""
    import httpx as _httpx

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_perf_comment(mobile, diff)

    if diff is not None:
        trend_text = (
            f"verbessert um {diff} Punkte" if diff > 2
            else f"verschlechtert um {abs(diff)} Punkte" if diff < -2
            else "stabil geblieben"
        )
    else:
        trend_text = "erste Messung"

    prompt = (
        f"Schreibe 2-3 Sätze als freundlicher Website-Berater für diesen Monatsbericht.\n"
        f"Firma: {company} | Website: {url}\n"
        f"PageSpeed Mobil: {mobile}/100 | Desktop: {desktop}/100\n"
        f"Trend: {trend_text}\n\n"
        f"Ton: professionell, kurz, konkret. Ein positiver Aspekt, ein Verbesserungshinweis.\n"
        f"Max 60 Wörter. Kein HTML. Nur der Text."
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
                "max_tokens": 150,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20.0,
        )
        if resp.is_success:
            return resp.json()["content"][0]["text"].strip()
    except Exception:
        pass

    return _fallback_perf_comment(mobile, diff)


def _fallback_perf_comment(mobile: int, diff) -> str:
    if (mobile or 0) >= 85:
        return (
            "Ihre Website performt ausgezeichnet. "
            "Der hohe Score sorgt für bessere Google-Rankings "
            "und schnellere Ladezeiten für Ihre Besucher."
        )
    elif (mobile or 0) >= 70:
        return (
            "Ihre Website läuft gut. "
            "Mit einigen Optimierungen — etwa Bildkomprimierung — "
            "lässt sich der Score noch weiter verbessern."
        )
    return (
        "Ihre Website hat Optimierungsbedarf. "
        "Ein niedriger PageSpeed-Score kann sich negativ auf "
        "Google-Rankings und Absprungrate auswirken."
    )


def _build_report_email(
    company, website_url, mobile, desktop,
    last_mobile, mobile_diff, ki_kommentar,
    upsell, report_count,
) -> str:
    from datetime import datetime as _dt

    month = _dt.utcnow().strftime("%B %Y")
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

    trend_html = ""
    if mobile_diff is not None:
        if mobile_diff > 2:
            trend_html = (
                f'<span style="color:#059669;font-weight:700;">'
                f'&#9650; +{mobile_diff} Punkte gegenüber Vormonat</span>'
            )
        elif mobile_diff < -2:
            trend_html = (
                f'<span style="color:#DC2626;font-weight:700;">'
                f'&#9660; {mobile_diff} Punkte gegenüber Vormonat</span>'
            )
        else:
            trend_html = (
                f'<span style="color:#6B7280;">'
                f'&#9654; Stabil (&#177;{abs(mobile_diff)} Punkte)</span>'
            )

    upsell_html = ""
    if upsell:
        upsell_html = """
        <div style="background:#FEF3C7;border-left:4px solid #D97706;
                    padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;">
          <div style="font-weight:700;color:#92400E;margin-bottom:6px;">
            &#128161; Empfehlung: Website-Optimierung
          </div>
          <div style="font-size:13px;color:#92400E;line-height:1.6;">
            Ein Score unter 70 kostet Sie täglich potenzielle Kunden.
            Mit unserem <strong>Performance-Paket</strong> optimieren wir
            Ladezeiten, Bilder und technische Faktoren gezielt.<br><br>
            <a href="mailto:info@kompagnon.de" style="color:#92400E;font-weight:700;">
              Jetzt kostenloses Beratungsgespräch anfragen &#8594;
            </a>
          </div>
        </div>"""

    trend_block = (
        f'<div style="margin-bottom:16px;font-size:13px;">{trend_html}</div>'
        if trend_html else ""
    )

    return f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#1a2332;">
  <div style="background:#008EAA;padding:20px 24px;border-radius:8px 8px 0 0;">
    <div style="color:#fff;font-size:18px;font-weight:700;">KOMPAGNON</div>
    <div style="color:rgba(255,255,255,.75);font-size:13px;">
      Ihr monatlicher Website-Report &#8212; {month}
    </div>
  </div>
  <div style="padding:24px;background:#fff;
              border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
    <p style="margin:0 0 20px;font-size:15px;">
      Guten Tag, <strong>{company}</strong>,
    </p>
    <div style="display:flex;gap:16px;margin-bottom:20px;">
      <div style="flex:1;text-align:center;padding:16px;
                  background:#f8fafc;border-radius:8px;
                  border:2px solid {score_color};">
        <div style="font-size:11px;color:#6B7280;
                    text-transform:uppercase;margin-bottom:4px;">Mobil</div>
        <div style="font-size:36px;font-weight:800;color:{score_color};">{mobile}</div>
        <div style="font-size:12px;color:{score_color};font-weight:600;">{score_label}</div>
      </div>
      <div style="flex:1;text-align:center;padding:16px;
                  background:#f8fafc;border-radius:8px;">
        <div style="font-size:11px;color:#6B7280;
                    text-transform:uppercase;margin-bottom:4px;">Desktop</div>
        <div style="font-size:36px;font-weight:800;color:#374151;">{desktop or '&#8211;'}</div>
        <div style="font-size:12px;color:#6B7280;">Score /100</div>
      </div>
    </div>
    {trend_block}
    <div style="background:#F0F9FF;border-radius:8px;
                padding:14px 16px;margin-bottom:20px;">
      <div style="font-size:12px;font-weight:700;color:#0369A1;margin-bottom:6px;">
        &#128202; KI-Analyse
      </div>
      <div style="font-size:13px;color:#374151;line-height:1.7;">{ki_kommentar}</div>
    </div>
    {upsell_html}
    <div style="font-size:12px;color:#6B7280;margin-top:20px;">
      <a href="https://{website_url}" style="color:#008EAA;">{website_url}</a> &#183;
      Report #{report_count} &#183; Gemessen im {month}
    </div>
    <div style="margin-top:20px;padding-top:20px;
                border-top:1px solid #e2e8f0;font-size:12px;color:#6B7280;">
      <strong>KOMPAGNON Communications</strong><br>
      Bei Fragen:
      <a href="mailto:info@kompagnon.de" style="color:#008EAA;">info@kompagnon.de</a>
    </div>
  </div>
</div>"""


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
            "interval", minutes=15,
            id="netlify_dns_check_every_15min",
            replace_existing=True,
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
