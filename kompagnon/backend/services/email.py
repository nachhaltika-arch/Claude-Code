import smtplib, os, logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _cfg():
    return {
        "host":  os.getenv("SMTP_HOST", ""),
        "port":  int(os.getenv("SMTP_PORT", "587")),
        "user":  os.getenv("SMTP_USER", ""),
        "pw":    os.getenv("SMTP_PASSWORD", ""),
        "name":  os.getenv("SMTP_SENDER_NAME", "KOMPAGNON"),
        "from":  os.getenv("SMTP_SENDER_EMAIL", os.getenv("SMTP_USER", "")),
        "ssl":   os.getenv("SMTP_PORT", "587") == "465",
    }


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str = "",
    cc: str = "",
    reply_to: str = "",
) -> bool:
    """
    Sendet eine HTML-E-Mail via SMTP.
    Gibt True bei Erfolg, False bei Fehler zurück.
    Loggt Fehler — wirft keine Exception.
    """
    cfg = _cfg()
    if not cfg["host"] or not cfg["user"]:
        logger.warning(
            f"SMTP nicht konfiguriert — E-Mail an {to_email} übersprungen. "
            f"Bitte SMTP_HOST und SMTP_USER in Render setzen."
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{cfg['name']} <{cfg['from']}>"
        msg["To"]      = to_email
        if cc:
            msg["Cc"] = cc
        if reply_to:
            msg["Reply-To"] = reply_to

        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if cfg["ssl"]:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"])
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"])
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(cfg["user"], cfg["pw"])
        recipients = [to_email] + ([cc] if cc else [])
        server.sendmail(cfg["from"], recipients, msg.as_string())
        server.quit()

        logger.info(f"✓ E-Mail gesendet an {to_email}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP Authentifizierung fehlgeschlagen. "
            "Zugangsdaten in Render prüfen."
        )
        return False
    except smtplib.SMTPConnectError:
        logger.error(
            f"SMTP Verbindung zu {cfg['host']}:{cfg['port']} fehlgeschlagen."
        )
        return False
    except Exception as e:
        logger.error(f"E-Mail Fehler an {to_email}: {e}")
        return False


def send_test_email(to_email: str) -> dict:
    """Testversand mit vollständigem Status-Report."""
    cfg = _cfg()
    if not cfg["host"] or not cfg["user"]:
        return {
            "success": False,
            "error": "SMTP_HOST oder SMTP_USER nicht gesetzt",
            "config_check": {
                "SMTP_HOST":        cfg["host"] or "❌ FEHLT",
                "SMTP_PORT":        cfg["port"],
                "SMTP_USER":        cfg["user"] or "❌ FEHLT",
                "SMTP_PASSWORD":    "✓ gesetzt" if cfg["pw"] else "❌ FEHLT",
                "SMTP_SENDER_NAME": cfg["name"],
            }
        }

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto">
      <div style="background:#008eaa;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="color:white;margin:0">KOMPAGNON Test-E-Mail</h2>
      </div>
      <div style="padding:20px;background:#f8f9fa;border-radius:0 0 8px 8px">
        <p>SMTP-Konfiguration funktioniert. ✓</p>
        <p style="font-size:12px;color:#888">
          Gesendet: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}<br>
          Von: {cfg['from']}<br>
          Host: {cfg['host']}:{cfg['port']}
        </p>
      </div>
    </div>"""

    ok = send_email(to_email, "KOMPAGNON SMTP-Test ✓", html)
    return {
        "success": ok,
        "to":      to_email,
        "from":    cfg["from"],
        "host":    cfg["host"],
        "port":    cfg["port"],
        "error":   None if ok else "Versand fehlgeschlagen — Render-Logs prüfen",
    }
