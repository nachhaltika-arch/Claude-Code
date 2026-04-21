"""
VERALTET — Bitte direkt verwenden:
    from services.email import send_email

Diese Datei bleibt nur für Rückwärtskompatibilität erhalten.
Neue Aufrufer MÜSSEN services/email.py direkt importieren.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from services.email import send_email as _canonical_send_email

logger = logging.getLogger(__name__)


class EmailService:
    """Rückwärtskompatibilität. Nicht für neue Aufrufer verwenden."""

    def send_email(self, to: str, subject: str, body: str = "",
                   html: bool = False, **kwargs) -> bool:
        html_body = body if html else f"<pre>{body}</pre>"
        ok = _canonical_send_email(to_email=to, subject=subject, html_body=html_body)
        if not ok:
            logger.warning(f"E-Mail an {to} konnte nicht gesendet werden")
        return ok

    @staticmethod
    def log_communication(db: Session, project_id: int, email_type: str,
                          direction: str, subject: str, body: str = "",
                          is_automated: bool = False,
                          template_key: Optional[str] = None):
        try:
            from database import Communication
            comm = Communication(
                project_id=project_id,
                type="email",
                direction=direction,
                channel="email",
                subject=subject,
                body=body[:500] if body else "",
                is_automated=is_automated,
                template_key=template_key,
                sent_at=datetime.utcnow(),
            )
            db.add(comm)
            db.commit()
        except Exception as e:
            logger.warning(f"log_communication fehlgeschlagen: {e}")
            try:
                db.rollback()
            except Exception:
                pass


class MockEmailService(EmailService):
    """Nur für Tests. Sendet keine echten E-Mails."""
    sent_emails: list = []

    def send_email(self, to: str, subject: str, body: str = "", **kwargs) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        logger.info(f"[MOCK] E-Mail an {to}: {subject}")
        return True
