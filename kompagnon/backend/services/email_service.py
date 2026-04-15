"""
Veraltet — EmailService und MockEmailService delegieren an services/email.py.

services/email.py ist die einzige kanonische Stelle fuer E-Mail-Versand
(siehe dortiges `send_email`). Diese Datei bleibt aus Rueckwaerts-
Kompatibilitaet erhalten:

- `EmailService.send_email(...)` delegiert an `services.email.send_email`.
- `EmailService.log_communication(...)` bleibt als static method erhalten
  (schreibt in die Communication-Tabelle, hat nichts mit SMTP zu tun).
- `MockEmailService.send_email(...)` ist ein echter Mock (kein Versand,
  nur Log + sammelt Eintraege in `sent_emails`). Wird von
  automations/scheduler.py::_get_email_service() genutzt wenn die
  Env-Variable USE_MOCK_EMAIL=true gesetzt ist.

Neue Aufrufer sollten direkt `from services.email import send_email`
verwenden, nicht mehr diese Datei.
"""
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from services.email import send_email as _canonical_send_email
from database import Communication

logger = logging.getLogger(__name__)


class EmailService:
    """Rueckwaerts-kompatibler Wrapper fuer den kanonischen send_email."""

    def __init__(self, *args, **kwargs):
        # Konstruktor-Argumente (smtp_host, smtp_port etc.) werden ignoriert —
        # die kanonische send_email liest SMTP-Konfiguration direkt aus env.
        pass

    def send_email(
        self,
        to: str,
        subject: str,
        body: str = "",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
    ) -> bool:
        """Delegiert an services/email.py::send_email.

        Mapping der alten Parameter auf die kanonische Signatur:
          to      → to_email
          subject → subject
          body    → html_body (falls html=True) oder text_body (falls False)
          cc      → cc (erste Adresse, kanonisch ist ein String)
          bcc     → NICHT unterstuetzt von der kanonischen Funktion; wird
                    ignoriert. Legacy-Aufrufer die bcc brauchen, sollten
                    direkt smtplib verwenden.
        """
        # body wird als HTML behandelt wenn html=True, sonst als Plain-Text.
        # Die kanonische send_email erwartet html_body als Pflicht — wir
        # wrappen Plain-Text in ein minimales <pre> damit Zeilenumbrueche
        # im Mail-Client erhalten bleiben.
        if html:
            html_body = body
            text_body = ""
        else:
            text_body = body
            html_body = (
                "<pre style=\"font-family:-apple-system,sans-serif;"
                "font-size:14px;white-space:pre-wrap\">"
                + (body or "")
                + "</pre>"
            )

        cc_str = ""
        if cc:
            if isinstance(cc, list):
                cc_str = cc[0] if cc else ""
            else:
                cc_str = cc

        if bcc:
            logger.warning(
                "EmailService.send_email: bcc-Parameter wird von der "
                "kanonischen services.email.send_email nicht unterstuetzt "
                "und wurde ignoriert."
            )

        return _canonical_send_email(
            to_email=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            cc=cc_str,
        )

    @staticmethod
    def log_communication(
        db: Session,
        project_id: int,
        email_type: str,
        direction: str,
        subject: str,
        body: str,
        is_automated: bool = False,
        template_key: Optional[str] = None,
    ) -> Optional[Communication]:
        """Log email in Communication table. Unveraendert — hat nichts mit SMTP zu tun."""
        try:
            comm = Communication(
                project_id=project_id,
                type="email",
                direction=direction,
                channel="email",
                subject=subject,
                body=body,
                is_automated=is_automated,
                template_key=template_key,
                sent_at=datetime.utcnow(),
            )
            db.add(comm)
            db.commit()
            return comm
        except Exception as e:
            logger.error(f"Communication logging failed: {e}")
            return None


class MockEmailService(EmailService):
    """Echter Mock — kein Versand, nur Log und Eintragssammlung.

    Wird ueber USE_MOCK_EMAIL=true in Development aktiviert (siehe
    automations/scheduler.py::_get_email_service). Die gesammelten
    sent_emails koennen in Tests ueber get_sent_emails() abgefragt werden.
    """

    def __init__(self):
        super().__init__()
        self.sent_emails = []

    def send_email(
        self,
        to: str,
        subject: str,
        body: str = "",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
    ) -> bool:
        self.sent_emails.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "cc": cc,
                "bcc": bcc,
                "html": html,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        logger.info(f"[MOCK] Email an {to}: {subject}")
        return True

    def get_sent_emails(self):
        return self.sent_emails


# ═══════════════════════════════════════════════════════════════════════════
# Template-Wrapper (aus frueherem Root-Level `backend/email_service.py`)
# ═══════════════════════════════════════════════════════════════════════════
# Diese drei Helper waren historisch in einer zweiten `email_service.py` im
# Backend-Root. Das war eine stille Duplikations-Falle: zwei Dateien mit
# identischem Namen auf zwei Ebenen. Der Merge hierher (Bug #2) macht
# `services/email_service.py` zur einzigen kanonischen Stelle.
#
# Die Wrapper bauen vordefinierte HTML-Mails und delegieren an die
# kanonische `services.email.send_email`. Sie sind thin wrappers — neue
# Aufrufer sollten direkt `send_email(to_email=..., subject=..., html_body=...)`
# aus `services/email.py` nutzen.

PHASE_NAMES = {
    1: "Akquise",
    2: "Briefing",
    3: "Content",
    4: "Technik",
    5: "QA",
    6: "Go-Live",
    7: "Post-Launch",
}


def send_phase_change_email(to: str, company: str, phase: int) -> bool:
    """Benachrichtigt einen Kunden ueber den Uebergang in eine neue Projekt-Phase."""
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
    """Benachrichtigt einen Kunden, dass sein Website-Audit abgeschlossen ist."""
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
    """Fordert einen Kunden zur Freigabe auf — z.B. fuer Content oder Design."""
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
