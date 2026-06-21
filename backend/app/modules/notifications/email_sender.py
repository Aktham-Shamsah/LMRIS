from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import get_settings


class EmailNotConfiguredError(RuntimeError):
    pass


class EmailSender:
    def send(self, *, to_email: str, subject: str, body: str) -> None:
        settings = get_settings()
        if not settings.email_enabled:
            raise EmailNotConfiguredError("Email delivery is disabled.")
        if not settings.smtp_host or not settings.mail_from:
            raise EmailNotConfiguredError("SMTP_HOST and MAIL_FROM are required when email is enabled.")

        actual_recipient = settings.email_redirect_to or to_email
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((settings.mail_from_name, settings.mail_from))
        message["To"] = actual_recipient
        if settings.reply_to:
            message["Reply-To"] = settings.reply_to
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
