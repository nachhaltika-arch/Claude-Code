"""
Veraltet — delegiert an services/email.py.
Nur für Rückwärtskompatibilität erhalten. Nicht für neue Aufrufer verwenden.
"""
import logging
from services.email import send_email as _send_email

logger = logging.getLogger(__name__)

PHASE_NAMES = {
    1: "Akquise", 2: "Briefing", 3: "Content",
    4: "Technik", 5: "QA", 6: "Go-Live", 7: "Post-Launch"
}


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Delegiert an services/email.py."""
    return _send_email(to_email=to, subject=subject, html_body=html_body)


def send_phase_change_email(to: str, company: str, phase: int):
    name = PHASE_NAMES.get(phase, f"Phase {phase}")
    subject = f"Ihr Projekt ist jetzt in Phase {phase}: {name}"
    body = f"""
    <h2>Gute Neuigkeiten, {company}!</h2>
    <p>Ihr Projekt ist in die nächste Phase übergegangen:</p>
    <h3>Phase {phase} von 7 — {name}</h3>
    <p>Mit freundlichen Grüßen,<br>Ihr KOMPAGNON-Team</p>
    """
    _send_email(to_email=to, subject=subject, html_body=body)


def send_audit_done_email(to: str, company: str, report_url: str = None):
    subject = f"Ihr Website-Audit für {company} ist fertig"
    link = f'<a href="{report_url}">Zum Audit-Report</a>' if report_url else ""
    body = f"""
    <h2>Ihr Audit-Bericht ist bereit, {company}!</h2>
    <p>Wir haben Ihre Website analysiert und den Bericht erstellt.</p>
    {link}
    <p>Mit freundlichen Grüßen,<br>Ihr KOMPAGNON-Team</p>
    """
    _send_email(to_email=to, subject=subject, html_body=body)


def send_approval_request_email(to: str, company: str, topic: str, notes: str = ""):
    subject = f"Ihre Freigabe wird benötigt – {topic}"
    body = f"""
    <h2>Freigabe erforderlich, {company}!</h2>
    <p>Für den nächsten Schritt benötigen wir Ihre Freigabe: <strong>{topic}</strong></p>
    {"<p>" + notes + "</p>" if notes else ""}
    <p>Mit freundlichen Grüßen,<br>Ihr KOMPAGNON-Team</p>
    """
    _send_email(to_email=to, subject=subject, html_body=body)
