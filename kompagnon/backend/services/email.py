"""
Email sending service via SMTP.
Includes password reset and welcome email templates.
"""
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "", attachment_path: str = None) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    sender_name = os.getenv("SMTP_SENDER_NAME", "KOMPAGNON")
    sender_email = os.getenv("SMTP_SENDER_EMAIL", smtp_user)

    if not smtp_host or not smtp_user:
        logger.warning("SMTP nicht konfiguriert — E-Mail nicht gesendet")
        return False

    try:
        msg = MIMEMultipart("mixed")
        body_part = MIMEMultipart("alternative")
        if text_body:
            body_part.attach(MIMEText(text_body, "plain", "utf-8"))
        body_part.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(body_part)
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email

        if attachment_path and os.path.isfile(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        logger.info(f"E-Mail gesendet an {to_email}")
        return True
    except Exception as e:
        logger.error(f"E-Mail Fehler an {to_email}: {e}")
        return False


def send_password_reset_email(to_email: str, reset_token: str, user_name: str = "") -> bool:
    frontend_url = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    name = user_name or "Nutzer"

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f0f2f8;font-family:system-ui,sans-serif;">
<div style="max-width:560px;margin:40px auto;padding:0 20px;">
<div style="background:#0F1E3A;border-radius:12px 12px 0 0;padding:28px 32px;text-align:center;">
<span style="color:#fff;font-weight:800;font-size:20px;">KOMPAGNON</span></div>
<div style="background:#fff;padding:36px 32px;border:1px solid #e2e8f0;border-top:none;">
<h2 style="margin:0 0 12px;font-size:22px;font-weight:800;color:#0F1E3A;">Passwort zuruecksetzen</h2>
<p style="font-size:15px;color:#475569;line-height:1.6;">Hallo {name},<br><br>
Sie haben eine Anfrage zum Zuruecksetzen Ihres Passworts gestellt.</p>
<div style="text-align:center;margin:32px 0;">
<a href="{reset_url}" style="display:inline-block;background:#0F1E3A;color:#fff;text-decoration:none;
padding:14px 36px;border-radius:8px;font-size:15px;font-weight:700;">Passwort zuruecksetzen</a></div>
<div style="background:#f8fafc;border-radius:8px;padding:16px 20px;margin:24px 0;">
<p style="margin:0 0 8px;font-size:13px;color:#64748b;">Dieser Link ist 1 Stunde gueltig.</p>
<p style="margin:0;font-size:13px;color:#64748b;">Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail.</p></div>
<p style="font-size:11px;color:#64748b;word-break:break-all;">Link: {reset_url}</p></div>
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;
padding:16px 32px;text-align:center;"><p style="margin:0;font-size:12px;color:#94a3b8;">2026 KOMPAGNON</p></div>
</div></body></html>"""

    return send_email(to_email, "Passwort zuruecksetzen — KOMPAGNON", html,
        f"Hallo {name},\n\nLink zum Zuruecksetzen: {reset_url}\n\nGueltig fuer 1 Stunde.\n\nKOMPAGNON")


def send_welcome_email(to_email: str, user_name: str = "", temp_password: str = "") -> bool:
    frontend_url = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")
    name = user_name or "Nutzer"
    pw_block = f"<p style='font-size:13px;color:#475569;'>Passwort: <strong>{temp_password}</strong></p>" if temp_password else ""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f0f2f8;font-family:system-ui,sans-serif;">
<div style="max-width:560px;margin:40px auto;padding:0 20px;">
<div style="background:#0F1E3A;border-radius:12px 12px 0 0;padding:28px 32px;text-align:center;">
<span style="color:#fff;font-weight:800;font-size:20px;">Willkommen bei KOMPAGNON</span></div>
<div style="background:#fff;padding:36px 32px;border:1px solid #e2e8f0;border-top:none;">
<p style="font-size:15px;color:#475569;line-height:1.6;">Hallo {name},<br>Ihr Konto wurde angelegt.</p>
{pw_block}
<div style="text-align:center;margin:28px 0;">
<a href="{frontend_url}/login" style="display:inline-block;background:#0F1E3A;color:#fff;text-decoration:none;
padding:14px 36px;border-radius:8px;font-size:15px;font-weight:700;">Jetzt einloggen</a></div></div>
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;
padding:16px 32px;text-align:center;"><p style="margin:0;font-size:12px;color:#94a3b8;">2026 KOMPAGNON</p></div>
</div></body></html>"""

    return send_email(to_email, "Willkommen bei KOMPAGNON", html)
