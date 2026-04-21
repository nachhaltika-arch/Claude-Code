"""
VERALTET — Bitte direkt verwenden:
    from services.email import send_email

Diese Datei bleibt nur fuer Rueckwaertskompatibilitaet erhalten.
Neue Aufrufer MUESSEN services/email.py direkt importieren.
"""
import logging
from services.email import send_email as _canonical_send_email
from database import Communication
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List

logger = logging.getLogger(__name__)


class EmailService:
    def send_email(self, to: str, subject: str, body: str = "",
                   cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                   html: bool = False, **kwargs) -> bool:
        html_body = body if html else f"<pre>{body}</pre>"
        return _canonical_send_email(to_email=to, subject=subject, html_body=html_body)

    @staticmethod
    def log_communication(db: Session, project_id: int, email_type: str,
                          direction: str, subject: str, body: str,
                          is_automated: bool = False, template_key: Optional[str] = None):
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
        except Exception as e:
            logger.warning(f"log_communication fehlgeschlagen: {e}")
            try:
                db.rollback()
            except Exception:
                pass


class MockEmailService(EmailService):
    sent_emails = []

    def send_email(self, to: str, subject: str, body: str = "", **kwargs) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        logger.info(f"[MOCK] E-Mail an {to}: {subject}")
        return True
