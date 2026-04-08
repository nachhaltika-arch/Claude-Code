from database import SessionLocal, Lead
from services.email import send_email
from services.email_templates import SEQUENZ_TEMPLATES, render
from sqlalchemy import text
from datetime import datetime, timedelta
import logging, os

logger = logging.getLogger(__name__)

SEQUENCE_DELAYS = {1: 0, 2: 3, 3: 7}
# Schritt 1 sofort, Schritt 2 nach 3 Tagen, Schritt 3 nach 7 Tagen


def run_email_sequences():
    """
    Wird stündlich vom Scheduler aufgerufen.
    Prüft alle Leads mit aktiver Sequenz und sendet die nächste E-Mail.
    """
    db = SessionLocal()
    try:
        leads = db.query(Lead).filter(
            Lead.sequence_active == True,
            Lead.sequence_paused == False,
            Lead.email != None,
            Lead.email != "",
        ).all()

        sent_count = 0
        for lead in leads:
            step      = lead.sequence_step or 0
            last_sent = lead.sequence_last_sent
            now       = datetime.utcnow()

            # Schritt 1 (step=0): sofort senden
            # Schritt 2 (step=1): nach 3 Tagen
            # Schritt 3 (step=2): nach 7 Tagen
            # step=3: Sequenz beendet

            if step >= 3:
                lead.sequence_active = False
                db.commit()
                continue

            delay_days = SEQUENCE_DELAYS.get(step + 1, 999)
            if last_sent and (now - last_sent).days < delay_days:
                continue  # Noch nicht Zeit

            template_key = f"sequence_step_{step + 1}"

            # Platzhalter befüllen
            domain = ""
            if lead.website_url:
                domain = (
                    lead.website_url
                    .replace("https://", "")
                    .replace("http://", "")
                    .replace("www.", "")
                    .split("/")[0]
                )

            tipps = _build_tipps(lead)
            data = {
                "firma":       lead.company_name or lead.email or "dort",
                "domain":      domain or lead.website_url or "",
                "top_problem": _get_top_problem(lead),
                "tipps_html":  tipps,
            }

            rendered = render(template_key, data)
            ok = send_email(
                to_email  = lead.email,
                subject   = rendered["subject"],
                html_body = rendered["html"],
            )

            # Protokoll
            db.execute(text("""
                INSERT INTO email_logs
                    (lead_id, to_email, subject, template_key, status)
                VALUES
                    (:lid, :to, :sub, :tpl, :status)
            """), {
                "lid":    lead.id,
                "to":     lead.email,
                "sub":    rendered["subject"],
                "tpl":    template_key,
                "status": "sent" if ok else "failed",
            })

            if ok:
                lead.sequence_step      = step + 1
                lead.sequence_last_sent = now
                sent_count += 1

            db.commit()

        logger.info(f"E-Mail-Sequenz: {sent_count} E-Mails gesendet")
        return sent_count

    except Exception as e:
        logger.error(f"Sequenz-Runner Fehler: {e}")
        return 0
    finally:
        db.close()


def _get_top_problem(lead) -> str:
    """Bestes Problem aus AI-Summary oder Fallback."""
    summary = getattr(lead, "ai_summary", "") or ""
    if summary:
        lines = [l.strip() for l in summary.split(".") if l.strip()]
        return lines[0] if lines else "Optimierungspotenzial bei SEO und Performance"
    return "Fehlende lokale SEO-Optimierung für Handwerksbetriebe"


def _build_tipps(lead) -> str:
    """3 Tipps als HTML-Liste."""
    tipps = [
        ("SEO-Optimierung", "Lokale Keywords für Ihre Region und Ihr Gewerk"),
        ("Performance",     "Ladezeit unter 3 Sekunden für bessere Google-Rankings"),
        ("Mobile Design",   "Über 60% der Anfragen kommen vom Smartphone"),
    ]
    html = ""
    for i, (titel, beschreibung) in enumerate(tipps, 1):
        html += f"""
        <div style="display:flex;gap:12px;margin-bottom:14px">
          <div style="width:28px;height:28px;border-radius:50%;
                      background:#1D9E75;color:white;font-weight:700;
                      font-size:13px;display:flex;align-items:center;
                      justify-content:center;flex-shrink:0">{i}</div>
          <div>
            <div style="font-weight:600;font-size:13px;
                        color:#1a2332">{titel}</div>
            <div style="font-size:13px;color:#64748b;margin-top:2px">
              {beschreibung}
            </div>
          </div>
        </div>"""
    return html


def start_sequence_for_lead(lead_id: int):
    """Startet die Sequenz für einen einzelnen Lead (manuell oder automatisch)."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or not lead.email:
            return False
        lead.sequence_active    = True
        lead.sequence_step      = 0
        lead.sequence_paused    = False
        lead.sequence_last_sent = None
        db.commit()
        logger.info(f"Sequenz gestartet für Lead {lead_id} ({lead.email})")
        return True
    except Exception as e:
        logger.error(f"Sequenz-Start Fehler: {e}")
        return False
    finally:
        db.close()
