"""
Email sending service via SMTP.
Includes password reset and welcome email templates.
"""
import smtplib
import os
import logging
from services.base_urls import public_base_url
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


def anhang_aus_datei(pfad, name: str = "") -> list:
    """Eine Datei als Anhang, in der Form, die `send_email` erwartet.

    **Warum es diesen Helfer gibt (26.08.2026).** Zwei Aufrufstellen riefen
    `send_email(..., attachment_path=...)` — ein Schluesselwort, das es hier
    nie gab. Python meldet das erst zur Laufzeit, beide Stellen fingen breit
    ab, und damit ging **die ganze Mail** nicht raus, nicht bloss der Anhang.
    Der naheliegende Name war also der falsche; statt die Unterschrift um ein
    zweites Verfahren zu erweitern, gibt es jetzt einen Weg vom Pfad zur
    erwarteten Form.

    **Eine fehlende Datei verhindert die Mail nicht.** Sie ist der Beiwerk,
    die Nachricht ist die Hauptsache — eine Willkommensmail ohne Anhang ist
    immer noch eine Willkommensmail.
    """
    import os

    if not pfad or not os.path.exists(pfad):
        if pfad:
            logger.warning("Anhang nicht gefunden, Mail geht ohne: %s", pfad)
        return []

    with open(pfad, "rb") as datei:
        inhalt = datei.read()
    dateiname = name or os.path.basename(pfad)
    untertyp = (os.path.splitext(dateiname)[1].lstrip(".") or "octet-stream")
    return [(dateiname, inhalt, untertyp)]


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "",
               db=None, attachments=None) -> bool:
    """Versendet eine E-Mail.

    attachments: Liste aus (Dateiname, Bytes, Untertyp), z. B.
    [("Bericht.pdf", pdf_bytes, "pdf")].

    Bevorzugt wird die Brevo-Transaktions-API, weil deren Schlüssel ohnehin
    für die Newsletter gepflegt wird. SMTP bleibt als zweiter Weg bestehen,
    falls jemand lieber einen eigenen Mailserver nutzt.
    """
    erfolg, _ = send_email_detailed(to_email, subject, html_body, text_body,
                                    db, attachments)
    return erfolg


def send_email_detailed(to_email: str, subject: str, html_body: str,
                        text_body: str = "", db=None, attachments=None) -> tuple:
    """Wie send_email, gibt aber (erfolg, begruendung) zurück.

    Ohne die Begründung landet der Grund nur im Server-Log — und wer keinen
    Log-Zugang hat, sieht bloß "Versand fehlgeschlagen" und kann nichts tun.
    """
    config = _smtp_settings(db)
    brevo_fehler = ""

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
            return True, "über Brevo gesendet"
        # Kein stiller Rückfall: ist SMTP nicht eingerichtet, bleibt es beim
        # Fehler — sonst sieht es aus, als sei nur SMTP nicht konfiguriert.
        logger.warning(f"Brevo-Versand fehlgeschlagen ({meldung})")
        brevo_fehler = f"Brevo: {meldung}"
        if not config["configured"]:
            return False, brevo_fehler
        logger.info("Versuche stattdessen SMTP")

    smtp_host = config["host"]
    smtp_port = config["port"]
    smtp_user = config["user"]
    smtp_pass = config["password"]
    sender_name = config["sender_name"]
    sender_email = config["sender_email"] or smtp_user

    if not config["configured"]:
        logger.warning("SMTP nicht konfiguriert — E-Mail nicht gesendet")
        return False, "Kein Versandweg eingerichtet (weder Brevo noch SMTP)"

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
        return True, "über SMTP gesendet"
    except Exception as e:
        logger.error(f"E-Mail Fehler an {to_email}: {e}")
        smtp_fehler = f"SMTP: {type(e).__name__}: {e}"[:200]
        # Beide Wege benennen — sonst sieht man nur den zuletzt versuchten
        # und sucht am falschen Ende.
        return False, f"{brevo_fehler} | {smtp_fehler}" if brevo_fehler else smtp_fehler


def _briefbogen(titel: str, absatz: str, knopf: str, url: str,
                hinweise: tuple = ()) -> str:
    """Der gemeinsame Briefbogen fuer jede Mail, die zu einem Link fuehrt.

    Er stand am 25.08.2026 zweimal fast gleich im Code — einmal fuer das
    Zuruecksetzen, und die Einladung haette ihn ein drittes Mal kopiert.
    Drei Kopien driften; die Fussnote „1 Stunde gueltig" waere in der
    Einladung schlicht falsch gewesen, und niemand haette es gemerkt.
    """
    fussnoten = "".join(
        f'<p style="margin:0 0 8px;font-size:13px;color:#64748b;">{h}</p>'
        for h in hinweise)
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f0f2f8;font-family:system-ui,sans-serif;">
<div style="max-width:560px;margin:40px auto;padding:0 20px;">
<div style="background:#0F1E3A;border-radius:12px 12px 0 0;padding:28px 32px;text-align:center;">
<span style="color:#fff;font-weight:800;font-size:20px;">KOMPAGNON</span></div>
<div style="background:#fff;padding:36px 32px;border:1px solid #e2e8f0;border-top:none;">
<h2 style="margin:0 0 12px;font-size:22px;font-weight:800;color:#0F1E3A;">{titel}</h2>
<p style="font-size:15px;color:#475569;line-height:1.6;">{absatz}</p>
<div style="text-align:center;margin:32px 0;">
<a href="{url}" style="display:inline-block;background:#0F1E3A;color:#fff;text-decoration:none;
padding:14px 36px;border-radius:8px;font-size:15px;font-weight:700;">{knopf}</a></div>
<div style="background:#f8fafc;border-radius:8px;padding:16px 20px;margin:24px 0;">{fussnoten}</div>
<p style="font-size:11px;color:#64748b;word-break:break-all;">Link: {url}</p></div>
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;
padding:16px 32px;text-align:center;"><p style="margin:0;font-size:12px;color:#94a3b8;">2026 KOMPAGNON</p></div>
</div></body></html>"""


def send_password_reset_email(to_email: str, reset_token: str, user_name: str = "") -> bool:
    reset_url = f"{public_base_url()}/reset-password?token={reset_token}"
    name = user_name or "Nutzer"

    html = _briefbogen(
        "Passwort zuruecksetzen",
        f"Hallo {name},<br><br>Sie haben eine Anfrage zum Zuruecksetzen "
        f"Ihres Passworts gestellt.",
        "Passwort zuruecksetzen", reset_url,
        ("Dieser Link ist 1 Stunde gueltig.",
         "Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail."))

    return send_email(to_email, "Passwort zuruecksetzen — KOMPAGNON", html,
        f"Hallo {name},\n\nLink zum Zuruecksetzen: {reset_url}\n\nGueltig fuer 1 Stunde.\n\nKOMPAGNON")


def send_einladung_email(to_email: str, token: str, betrieb: str,
                         name: str = "", tage: int = 7) -> bool:
    """Der Brief, mit dem ein zweiter Mensch an einen Betrieb kommt.

    Er nennt **den Betrieb**. Wer eingeladen wird, hat oft mit mehreren
    Firmen zu tun; „Sie wurden eingeladen" allein beantwortet nicht, wozu.
    """
    url = f"{public_base_url()}/reset-password?token={token}"
    anrede = name or "Sie"

    html = _briefbogen(
        "Ihr Zugang zu KOMPAGNON",
        f"Hallo {anrede},<br><br>fuer <strong>{betrieb}</strong> wurde Ihnen "
        f"ein eigener Zugang zu KOMPAGNON eingerichtet. Vergeben Sie hier Ihr "
        f"Passwort, dann koennen Sie sich mit dieser E-Mail-Adresse anmelden.",
        "Passwort vergeben", url,
        (f"Dieser Link ist {tage} Tage gueltig.",
         "Danach fordern Sie ueber „Passwort vergessen“ einen neuen an."))

    return send_email(to_email, f"Ihr Zugang zu KOMPAGNON — {betrieb}", html,
        f"Hallo {anrede},\n\nfuer {betrieb} wurde Ihnen ein Zugang eingerichtet.\n"
        f"Passwort vergeben: {url}\n\nGueltig fuer {tage} Tage.\n\nKOMPAGNON")


def send_welcome_email(to_email: str, user_name: str = "", temp_password: str = "") -> bool:
    frontend_url = public_base_url()
    name = user_name or "Nutzer"
    pw_block = f"<p style='font-size:13px;color:#475569;'>Passwort: <strong>{temp_password}</strong></p>" if temp_password else ""

    html = f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"></head>
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
