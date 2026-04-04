import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "KOMPAGNON <noreply@kompagnon.de>")

PHASE_NAMES = {
    1: "Akquise", 2: "Briefing", 3: "Content",
    4: "Technik", 5: "QA", 6: "Go-Live", 7: "Post-Launch"
}

def send_email(to: str, subject: str, html_body: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[Email] SMTP nicht konfiguriert – E-Mail übersprungen.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to, msg.as_string())
    print(f"[Email] Gesendet an {to}: {subject}")

def send_phase_change_email(to: str, company: str, phase: int):
    name = PHASE_NAMES.get(phase, f"Phase {phase}")
    subject = f"Ihr Projekt ist jetzt in Phase {phase}: {name}"
    body = f"""
    <h2>Gute Neuigkeiten, {company}!</h2>
    <p>Ihr Projekt ist in die nächste Phase übergegangen:</p>
    <h3>Phase {phase} von 7 — {name}</h3>
    <p>Wir halten Sie auf dem Laufenden. Bei Fragen stehen wir jederzeit zur Verfügung.</p>
    <p>Mit freundlichen Grüßen,<br>Ihr KOMPAGNON-Team</p>
    """
    send_email(to, subject, body)

def send_audit_done_email(to: str, company: str, report_url: str = None):
    subject = f"Ihr Website-Audit für {company} ist fertig"
    link = f'<a href="{report_url}">Zum Audit-Report</a>' if report_url else ""
    body = f"""
    <h2>Ihr Audit-Bericht ist bereit, {company}!</h2>
    <p>Wir haben Ihre Website analysiert und den Bericht erstellt.</p>
    {link}
    <p>Mit freundlichen Grüßen,<br>Ihr KOMPAGNON-Team</p>
    """
    send_email(to, subject, body)

def send_approval_request_email(to: str, company: str, topic: str, notes: str = ""):
    subject = f"Ihre Freigabe wird benötigt – {topic}"
    body = f"""
    <h2>Freigabe erforderlich, {company}!</h2>
    <p>Für den nächsten Schritt in Ihrem Projekt benötigen wir Ihre Freigabe:</p>
    <h3>{topic}</h3>
    {"<p>" + notes + "</p>" if notes else ""}
    <p>Bitte antworten Sie auf diese E-Mail oder kontaktieren Sie uns direkt.</p>
    <p>Mit freundlichen Grüßen,<br>Ihr KOMPAGNON-Team</p>
    """
    send_email(to, subject, body)
