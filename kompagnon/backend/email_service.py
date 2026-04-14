"""
Veraltet — delegiert an services/email.py.

Nur fuer Rueckwaertskompatibilitaet erhalten. Neue Aufrufer sollten
direkt `from services.email import send_email` verwenden.
"""
import logging
from services.email import send_email as _canonical_send_email

logger = logging.getLogger(__name__)

PHASE_NAMES = {
    1: "Akquise",
    2: "Briefing",
    3: "Content",
    4: "Technik",
    5: "QA",
    6: "Go-Live",
    7: "Post-Launch",
}


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Delegiert an services/email.py::send_email.

    Wrapper-Signatur nutzt `to` statt `to_email` fuer Rueckwaerts-
    kompatibilitaet mit den zwei Aufrufern (routers/audit.py,
    routers/projects.py) die die alte Parameterform nutzen.
    """
    return _canonical_send_email(to_email=to, subject=subject, html_body=html_body)


def send_phase_change_email(to: str, company: str, phase: int) -> bool:
    name = PHASE_NAMES.get(phase, f"Phase {phase}")
    subject = f"Ihr Projekt ist jetzt in Phase {phase}: {name}"
    body = f"""
    <h2>Gute Neuigkeiten, {company}!</h2>
    <p>Ihr Projekt ist in die naechste Phase uebergegangen:</p>
    <h3>Phase {phase} von 7 — {name}</h3>
    <p>Wir halten Sie auf dem Laufenden. Bei Fragen stehen wir jederzeit zur Verfuegung.</p>
    <p>Mit freundlichen Gruessen,<br>Ihr KOMPAGNON-Team</p>
    """
    return _canonical_send_email(to_email=to, subject=subject, html_body=body)


def send_audit_done_email(to: str, company: str, report_url: str = None) -> bool:
    subject = f"Ihr Website-Audit fuer {company} ist fertig"
    link = f'<a href="{report_url}">Zum Audit-Report</a>' if report_url else ""
    body = f"""
    <h2>Ihr Audit-Bericht ist bereit, {company}!</h2>
    <p>Wir haben Ihre Website analysiert und den Bericht erstellt.</p>
    {link}
    <p>Mit freundlichen Gruessen,<br>Ihr KOMPAGNON-Team</p>
    """
    return _canonical_send_email(to_email=to, subject=subject, html_body=body)


def send_approval_request_email(to: str, company: str, topic: str, notes: str = "") -> bool:
    subject = f"Ihre Freigabe wird benoetigt \u2014 {topic}"
    notes_html = "<p>" + notes + "</p>" if notes else ""
    body = f"""
    <h2>Freigabe erforderlich, {company}!</h2>
    <p>Fuer den naechsten Schritt in Ihrem Projekt benoetigen wir Ihre Freigabe:</p>
    <h3>{topic}</h3>
    {notes_html}
    <p>Bitte antworten Sie auf diese E-Mail oder kontaktieren Sie uns direkt.</p>
    <p>Mit freundlichen Gruessen,<br>Ihr KOMPAGNON-Team</p>
    """
    return _canonical_send_email(to_email=to, subject=subject, html_body=body)
