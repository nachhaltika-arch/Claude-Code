"""Was technisch nachgesehen wird: DNS, Zertifikate, Domains (L-25).

**Warum eigene Datei, 22.08.2026.** `automations/scheduler.py` hatte 1.468
Zeilen und darin vier Dinge: die Zeitsteuerung selbst, die Kundenmails, die
technische Ueberwachung und den Monatsbericht. Fuenf Auftraege, davon einer mit 213 Zeilen: die DNS-Pruefung der
Netlify-Seiten. Sie haben mit dem Kundenkontakt nichts zu tun ausser der
Mail, die sie im Alarmfall schicken.

Transitiv gemessen, ohne die Infrastruktur — die Klasse `CompagnonScheduler`
nennt **jeden** Auftragsnamen, und eine Messung, die ueber sie laeuft, zieht
darum die ganze Datei nach. Das war der erste Anlauf: 1.328 von 1.468
Zeilen, was offensichtlich falsch war.
"""
from datetime import datetime, timedelta
from database import SessionLocal, Project, Communication, DATABASE_URL
import logging

# Die Alarm-Mail kommt aus dem Kontakt-Teil — dieselbe Funktion, die
# auch die Kundenerinnerungen verschickt.
from automations.scheduler_kontakt import _do_send_email

logger = logging.getLogger(__name__)


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
                    # Bug #4 (phase_5 -> phase_6): Site ist live, also auch
                    # Project-Status auf phase_6 transitionen + actual_go_live
                    # setzen (falls noch null). Idempotent ueber den WHERE-Filter
                    # weiter oben (netlify_golive_mail_sent IS NULL/false), d.h.
                    # dieser Block laeuft pro Project nur einmal.
                    db.execute(_text("""
                        UPDATE projects SET
                          netlify_domain_status   = 'active',
                          netlify_ssl_active      = TRUE,
                          netlify_dns_fail_count  = 0,
                          netlify_dns_retry_after = NULL,
                          status                  = 'phase_6',
                          current_phase           = 6,
                          actual_go_live          = COALESCE(actual_go_live, NOW()),
                          updated_at              = NOW()
                        WHERE id = :id
                    """), {"id": project_id})

                    # Folge-Jobs (Day-5/14/21/30) schedulen
                    try:
                        # **Erst hier importiert.** `scheduler.py` holt die
                        # Auftraege aus dieser Datei; ein Import am Kopf
                        # waere ein Zirkelbezug. Gebraucht wird der
                        # Scheduler ohnehin erst zur Laufzeit.
                        from automations.scheduler import get_scheduler

                        get_scheduler().trigger_phase_change(project_id, "phase_6")
                    except Exception as tpc_err:
                        logger.warning(
                            f"trigger_phase_change(phase_6) Fehler "
                            f"Projekt {project_id}: {tpc_err}"
                        )
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
            # Ueber `_do_send_email`, nicht direkt: Dieser Aufruf ging bis zum
            # 17.08.2026 am gemeinsamen Weg vorbei und damit an jeder Sperre.
            # Eine Sperre, die ein Sender umgehen kann, ist keine.
            if _do_send_email(
                to_email=lead[0],
                subject=f"Wichtig: SSL-Zertifikat für {domain} benötigt Erneuerung",
                html_body=html_body,
            ):
                logger.info(f"SSL-Alert E-Mail gesendet an {lead[0]}")
    except Exception as e:
        logger.warning(f"SSL-Alert E-Mail Fehler: {e}")


async def _check_all_domains_async():
    # `Project` steht schon am Dateikopf; hier nur, was sonst fehlt.
    from database import Lead, SessionLocal
    from services.domain_checker import check_domain
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
