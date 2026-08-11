"""
Email sending service via SMTP.
Includes password reset and welcome email templates.
"""
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _smtp_settings(db=None) -> dict:
    """Zugang aus den Einstellungen im Tool, sonst aus den Umgebungsvariablen.

    Ohne eigene Session wird eine geöffnet und wieder geschlossen — der Versand
    läuft auch aus Hintergrundaufgaben ohne Request-Kontext.
    """
    try:
        from services.app_settings import smtp_config

        if db is not None:
            return smtp_config(db)

        from database import SessionLocal

        own = SessionLocal()
        try:
            return smtp_config(own)
        finally:
            own.close()
    except Exception as e:  # noqa: BLE001 — Rückfall auf reine Umgebungsvariablen
        logger.warning(f"SMTP-Einstellungen nicht lesbar ({e}) — nutze Umgebungsvariablen")
        user = os.getenv("SMTP_USER", "")
        host = os.getenv("SMTP_HOST", "")
        return {
            "host": host,
            "port": int(os.getenv("SMTP_PORT", "587") or 587),
            "user": user,
            "password": os.getenv("SMTP_PASSWORD", ""),
            "sender_name": os.getenv("SMTP_SENDER_NAME", "KOMPAGNON"),
            "sender_email": os.getenv("SMTP_SENDER_EMAIL", user),
            "configured": bool(host and user),
        }


def _build_message(subject: str, sender: str, to_email: str, html_body: str,
                   text_body: str, attachments):
    """Baut die Nachricht — mit Anhang als 'mixed', sonst als 'alternative'.

    Ein Anhang darf nicht in den alternative-Teil: Mail-Programme zeigen dort
    nur eine der Varianten an, der Anhang ginge verloren.
    """
    from email.mime.application import MIMEApplication

    inhalt = MIMEMultipart("alternative")
    if text_body:
        inhalt.attach(MIMEText(text_body, "plain", "utf-8"))
    inhalt.attach(MIMEText(html_body, "html", "utf-8"))

    if not attachments:
        inhalt["Subject"] = subject
        inhalt["From"] = sender
        inhalt["To"] = to_email
        return inhalt

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(inhalt)

    for dateiname, daten, subtyp in attachments:
        teil = MIMEApplication(daten, _subtype=subtyp)
        teil.add_header("Content-Disposition", "attachment", filename=dateiname)
        msg.attach(teil)

    return msg


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "",
               db=None, attachments=None) -> bool:
    """Versendet eine E-Mail.

    attachments: Liste aus (Dateiname, Bytes, Untertyp), z. B.
    [("Bericht.pdf", pdf_bytes, "pdf")].

    Bevorzugt wird die Brevo-Transaktions-API, weil deren Schlüssel ohnehin
    für die Newsletter gepflegt wird. SMTP bleibt als zweiter Weg bestehen,
    falls jemand lieber einen eigenen Mailserver nutzt.
    """
    config = _smtp_settings(db)

    from services import brevo_mail

    if brevo_mail.is_available():
        erfolg, meldung = brevo_mail.send(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender_name=config.get("sender_name") or "",
            sender_email=config.get("sender_email") or "",
            attachments=attachments,
        )
        if erfolg:
            return True
        # Kein stiller Rückfall: ist SMTP nicht eingerichtet, bleibt es beim
        # Fehler — sonst sieht es aus, als sei nur SMTP nicht konfiguriert.
        logger.warning(f"Brevo-Versand fehlgeschlagen ({meldung})")
        if not config["configured"]:
            return False
        logger.info("Versuche stattdessen SMTP")

    smtp_host = config["host"]
    smtp_port = config["port"]
    smtp_user = config["user"]
    smtp_pass = config["password"]
    sender_name = config["sender_name"]
    sender_email = config["sender_email"] or smtp_user

    if not config["configured"]:
        logger.warning("SMTP nicht konfiguriert — E-Mail nicht gesendet")
        return False

    try:
        msg = _build_message(
            subject=subject,
            sender=f"{sender_name} <{sender_email}>",
            to_email=to_email,
            html_body=html_body,
            text_body=text_body,
            attachments=attachments,
        )

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
