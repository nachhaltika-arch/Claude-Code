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
