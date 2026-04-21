"""
Spezialisierte E-Mail-Funktionen (Phasenwechsel, Audit, Freigabe).
Delegiert an services/email.send_email fuer den eigentlichen SMTP-Versand.
"""
import logging
from services.email import send_email

logger = logging.getLogger(__name__)

PHASE_NAMES = {
    1: "Akquise", 2: "Briefing", 3: "Content",
    4: "Technik", 5: "QA", 6: "Go-Live", 7: "Post-Launch"
}


def send_phase_change_email(to: str, company: str, phase: int):
    name = PHASE_NAMES.get(phase, f"Phase {phase}")
    subject = f"Ihr Projekt ist jetzt in Phase {phase}: {name}"
    body = f"""
    <h2>Gute Neuigkeiten, {company}!</h2>
    <p>Ihr Projekt ist in die naechste Phase uebergegangen:</p>
    <h3>Phase {phase} von 7 — {name}</h3>
    <p>Wir halten Sie auf dem Laufenden. Bei Fragen stehen wir jederzeit zur Verfuegung.</p>
    <p>Mit freundlichen Gruessen,<br>Ihr KOMPAGNON-Team</p>
    """
    ok = send_email(to_email=to, subject=subject, html_body=body)
    if not ok:
        logger.warning(f"Phase-E-Mail an {to} fehlgeschlagen")


def send_audit_done_email(to: str, company: str, report_url: str = None):
    subject = f"Ihr Website-Audit fuer {company} ist fertig"
    link = f'<a href="{report_url}">Zum Audit-Report</a>' if report_url else ""
    body = f"""
    <h2>Ihr Audit-Bericht ist bereit, {company}!</h2>
    <p>Wir haben Ihre Website analysiert und den Bericht erstellt.</p>
    {link}
    <p>Mit freundlichen Gruessen,<br>Ihr KOMPAGNON-Team</p>
    """
    ok = send_email(to_email=to, subject=subject, html_body=body)
    if not ok:
        logger.warning(f"Audit-E-Mail an {to} fehlgeschlagen")


def send_approval_request_email(to: str, company: str, topic: str, notes: str = ""):
    subject = f"Ihre Freigabe wird benoetigt — {topic}"
    body = f"""
    <h2>Freigabe erforderlich, {company}!</h2>
    <p>Fuer den naechsten Schritt in Ihrem Projekt benoetigen wir Ihre Freigabe:</p>
    <h3>{topic}</h3>
    {"<p>" + notes + "</p>" if notes else ""}
    <p>Bitte antworten Sie auf diese E-Mail oder kontaktieren Sie uns direkt.</p>
    <p>Mit freundlichen Gruessen,<br>Ihr KOMPAGNON-Team</p>
    """
    ok = send_email(to_email=to, subject=subject, html_body=body)
    if not ok:
        logger.warning(f"Freigabe-E-Mail an {to} fehlgeschlagen")
