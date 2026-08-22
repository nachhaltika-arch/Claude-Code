"""Was dem Kunden von selbst geschrieben wird (L-25).

**Warum eigene Datei, 22.08.2026.** `automations/scheduler.py` hatte 1.468
Zeilen und darin vier Dinge: die Zeitsteuerung selbst, die Kundenmails, die
technische Ueberwachung und den Monatsbericht. Zwoelf Auftraege, die alle dasselbe tun: nachsehen, ob etwas faellig ist,
und dann eine Mail schicken — Phasenerinnerung, fehlende Unterlagen,
Briefing-Erinnerung, die Tag-5-bis-30-Strecke.

Transitiv gemessen, ohne die Infrastruktur — die Klasse `CompagnonScheduler`
nennt **jeden** Auftragsnamen, und eine Messung, die ueber sie laeuft, zieht
darum die ganze Datei nach. Das war der erste Anlauf: 1.328 von 1.468
Zeilen, was offensichtlich falsch war.
"""
from datetime import datetime, timedelta
from database import SessionLocal, Project, Communication, DATABASE_URL
from services.base_urls import public_base_url
from services.email import send_email as _send_email_canonical
from services import versandsperre
from automations.email_templates import render_template
import os
from automations.versandmodus import probemodus
from automations.erinnerungen import BRIEFING_STUFEN
from automations.erinnerungen import MATERIAL_STUFEN
from automations.erinnerungen import faellige_erinnerung
import logging

logger = logging.getLogger(__name__)


def _do_send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Der gemeinsame Versandweg aller Scheduler-Jobs.

    Hier haengt seit dem 17.08.2026 die Versandsperre: Es ist die eine Stelle,
    durch die jede Mail geht, die ohne menschlichen Anlass entsteht. Wer sein
    Passwort zuruecksetzt oder im Widget etwas anfordert, kommt hier nicht
    vorbei — diese Mails bleiben unberuehrt.
    """
    if probemodus():
        logger.info(f"[MOCK] E-Mail an {to_email}: {subject}")
        return True

    if not versandsperre.in_eigener_sitzung_erlaubt():
        logger.warning(
            f"Versandsperre aktiv — nicht gesendet an {to_email}: {subject!r}"
        )
        return False

    return _send_email_canonical(to_email=to_email, subject=subject, html_body=html_body)


def _send_phase_email(project_id: int, template_key: str):
    """Send template email for a project (standalone function)."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project or not project.lead:
            return

        lead = project.lead
        frontend_url = public_base_url()
        # Token-Direktlink wenn vorhanden, sonst Login-Fallback. Verwendet
        # in Briefing-Remindern (Bug #5) und überall wo das Portal verlinkt wird.
        briefing_link = (
            f"{frontend_url}/portal/{lead.customer_token}"
            if lead.customer_token
            else f"{frontend_url}/portal/login"
        )
        context = {
            "company_name":         lead.company_name or "Ihr Unternehmen",
            "contact_name":         lead.contact_name or "liebe Kundin / lieber Kunde",
            "assigned_person":      "KOMPAGNON-Team",
            "contact_person_phone": os.getenv("CONTACT_PHONE", "+49 (0) 261 88 44 70"),
            "contact_person_email": os.getenv("CONTACT_EMAIL", "info@kompagnon.eu"),
            "preview_link":         briefing_link,
            "upload_link":          briefing_link,
            "briefing_link":        briefing_link,
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


def _bereits_gesendet(db, project_id: int) -> set:
    """Welche Vorlagen dieses Projekt schon bekommen hat."""
    zeilen = (
        db.query(Communication.template_key)
        .filter(Communication.project_id == project_id,
                Communication.template_key.isnot(None))
        .all()
    )
    return {z[0] for z in zeilen}


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
    """Erinnert einmal an fehlende Materialien — nicht jeden Morgen.

    Bis zum 17.08.2026 stand hier `if days_since_start > 5: _send_phase_email(...)`
    ohne jede Sperre. Der Job laeuft taeglich um 09:00, also ging die Mail an
    jedes Projekt in `phase_2` **jeden Tag erneut** raus. Ein Betrieb hat sie
    ueber 135 Tage bekommen. Die Staffelung liegt jetzt in
    `automations/erinnerungen.py` und gilt fuer beide Erinnerungs-Jobs.
    """
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.status == "phase_2").all()

        for project in projects:
            if not project.start_date:
                continue
            if not project.lead or not project.lead.email:
                continue

            tage = (datetime.utcnow() - project.start_date).days
            vorlage = faellige_erinnerung(
                tage, MATERIAL_STUFEN, _bereits_gesendet(db, project.id)
            )
            if not vorlage:
                continue

            logger.info(
                f"📧 Material-Erinnerung ({vorlage}) für Projekt {project.id} "
                f"(Tag {tage} ohne Materialien)"
            )
            _send_phase_email(project.id, vorlage)
    finally:
        db.close()


def job_send_briefing_reminders():
    """
    Bug #5: Sendet Briefing-Erinnerungen an phase_1-Projekte ohne eingereichtes
    Briefing. Idempotent über die Communication-Tabelle (template_key+project_id
    werden dort beim erfolgreichen Send geloggt).
    """
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(
            Project.status == "phase_1",
            Project.has_briefing.is_(False),
        ).all()

        if not projects:
            logger.info("Briefing-Reminder: keine offenen phase_1-Projekte")
            return

        logger.info(f"Briefing-Reminder: {len(projects)} phase_1-Projekte zu prüfen")

        for project in projects:
            if not project.start_date:
                continue
            if not project.lead or not project.lead.email:
                continue

            days_since = (datetime.utcnow() - project.start_date).days
            # Dieselbe Entscheidung wie beim Material-Job, seit 17.08.2026 an
            # einer Stelle: hoechste erreichte Stufe, jede genau einmal.
            template_key = faellige_erinnerung(
                days_since, BRIEFING_STUFEN, _bereits_gesendet(db, project.id)
            )
            if not template_key:
                continue

            logger.info(
                f"📧 Briefing-Reminder ({template_key}) für Projekt {project.id} "
                f"(Tag {days_since} ohne Briefing)"
            )
            _send_phase_email(project.id, template_key)
    finally:
        db.close()


def job_phase_postgolive_transitions():
    """
    Bug #4: Auto-Transitions nach Go-Live.
    - phase_6 -> phase_7 sieben Tage nach actual_go_live (Post-Launch-Phase)
    - phase_7 -> completed nach 30 Tagen post-Go-Live (Projekt formal abgeschlossen)
    Idempotent ueber den status-Filter im UPDATE — sobald sich der status aendert,
    faellt das Project aus dem naechsten Lauf.
    """
    from sqlalchemy import text as _text

    db = SessionLocal()
    try:
        rows_67 = db.execute(_text("""
            UPDATE projects
            SET status        = 'phase_7',
                current_phase = 7,
                updated_at    = NOW()
            WHERE status = 'phase_6'
              AND actual_go_live IS NOT NULL
              AND actual_go_live < NOW() - INTERVAL '7 days'
            RETURNING id
        """)).fetchall()
        for row in rows_67:
            logger.info(f"📅 Phase-Transition phase_6 -> phase_7 (Projekt {row[0]})")

        rows_7c = db.execute(_text("""
            UPDATE projects
            SET status        = 'completed',
                current_phase = 8,
                updated_at    = NOW()
            WHERE status = 'phase_7'
              AND actual_go_live IS NOT NULL
              AND actual_go_live < NOW() - INTERVAL '30 days'
            RETURNING id
        """)).fetchall()
        for row in rows_7c:
            logger.info(f"📅 Phase-Transition phase_7 -> completed (Projekt {row[0]})")

        db.commit()
    except Exception as e:
        logger.error(f"Phase-Postgolive-Transition Fehler: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


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
