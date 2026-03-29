"""
SMTP Email Service for sending automated emails.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from database import Communication


class EmailService:
    """Send emails via SMTP (Gmail, custom SMTP server, etc)."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "info@kompagnon.de")
        self.use_tls = self.smtp_port in [587, 25]

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to: Recipient email (comma-separated for multiple)
            subject: Email subject
            body: Email body
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ",".join(cc) if isinstance(cc, list) else cc

            # Add body
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type, "utf-8"))

            # Prepare recipient list
            recipients = to.split(",")
            if cc:
                recipients.extend(cc if isinstance(cc, list) else cc.split(","))
            if bcc:
                recipients.extend(bcc if isinstance(bcc, list) else bcc.split(","))

            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()

            return True

        except Exception as e:
            print(f"❌ Email send failed: {str(e)}")
            return False

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
        """Log email in Communication table."""
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
            print(f"❌ Communication logging failed: {str(e)}")
            return None


class MockEmailService(EmailService):
    """Mock email service for development (no actual sending)."""

    def __init__(self):
        super().__init__()
        self.sent_emails = []

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
    ) -> bool:
        """Log email instead of sending."""
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
        print(f"📧 [MOCK] Email to {to}: {subject}")
        return True

    def get_sent_emails(self):
        """Get list of all sent emails (for testing)."""
        return self.sent_emails
