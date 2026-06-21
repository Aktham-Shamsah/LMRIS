from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.db.mongo import get_db
from app.modules.notifications.email_sender import EmailSender
from app.shared.ids import utc_now
from app.shared.serialization import mongo_doc


STATUS_LABELS = {
    "submitted": "submitted",
    "pre_checked": "pre-checked",
    "survey_required": "ready for survey assignment",
    "surveyed": "survey completed",
    "legal_review": "under legal review",
    "approved": "approved",
    "certificate_issued": "certificate issued",
    "closed": "closed",
    "rejected": "rejected",
    "on_hold": "placed on hold",
    "missing_documents": "waiting for missing documents",
    "under_objection": "under objection",
}


class NotificationService:
    def __init__(self, db=None, email_sender: EmailSender | None = None) -> None:
        self.db = db if db is not None else get_db()
        self.email_sender = email_sender or EmailSender()

    def publish(
        self,
        *,
        event_type: str,
        subject: str,
        body: str,
        recipients: list[dict[str, Any]],
        application_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        now = utc_now()
        event = {
            "event_id": uuid.uuid4().hex,
            "event_type": event_type,
            "application_id": application_id,
            "subject": subject,
            "body": body,
            "recipients": recipients,
            "metadata": metadata or {},
            "created_at": now,
        }
        self.db.notification_events.insert_one(event)
        for recipient in recipients:
            if recipient.get("email"):
                self._queue_email(event, recipient)
        return mongo_doc(event)

    def application_submitted(self, app: dict) -> None:
        recipient = self._applicant_recipient(app)
        if not recipient:
            return
        self.publish(
            event_type="application.submitted",
            application_id=app["application_id"],
            subject=f"LRMIS application received: {app['application_id']}",
            body=(
                f"Hello {recipient.get('name') or 'Applicant'},\n\n"
                f"Your land registration application {app['application_id']} was submitted successfully.\n\n"
                "You can sign in to LRMIS to track updates."
            ),
            recipients=[recipient],
            metadata={"status": app.get("status")},
        )

    def application_status_changed(self, app: dict, previous_status: str, new_status: str, reason: str | None = None) -> None:
        recipient = self._applicant_recipient(app, new_status)
        if not recipient:
            return
        status_label = STATUS_LABELS.get(new_status, new_status.replace("_", " "))
        reason_line = f"\nReason: {reason}" if reason else ""
        self.publish(
            event_type="application.status_changed",
            application_id=app["application_id"],
            subject=f"LRMIS update for {app['application_id']}: {status_label}",
            body=(
                f"Hello {recipient.get('name') or 'Applicant'},\n\n"
                f"Your application {app['application_id']} is now {status_label}."
                f"{reason_line}\n\n"
                "Please sign in to LRMIS for the latest details."
            ),
            recipients=[recipient],
            metadata={"from": previous_status, "to": new_status, "reason": reason},
        )

    def send_test_email(self, to_email: str) -> dict:
        return self.publish(
            event_type="email.test",
            subject="LRMIS email delivery test",
            body="This is a test email from LRMIS SMTP notification delivery.",
            recipients=[{"email": to_email, "name": "LRMIS Admin"}],
            metadata={"manual": True},
        )

    def _queue_email(self, event: dict, recipient: dict[str, Any]) -> None:
        settings = get_settings()
        now = utc_now()
        message = {
            "message_id": uuid.uuid4().hex,
            "event_id": event["event_id"],
            "application_id": event.get("application_id"),
            "channel": "email",
            "to_email": recipient["email"],
            "subject": event["subject"],
            "body": event["body"],
            "status": "queued",
            "attempts": 0,
            "created_at": now,
            "updated_at": now,
            "last_error": None,
        }
        self.db.notification_messages.insert_one(message)
        if settings.email_enabled and settings.email_send_immediately:
            self._send_email_message(message)

    def _send_email_message(self, message: dict[str, Any]) -> None:
        attempts = int(message.get("attempts", 0)) + 1
        update: dict[str, Any] = {"attempts": attempts, "updated_at": utc_now()}
        try:
            self.email_sender.send(to_email=message["to_email"], subject=message["subject"], body=message["body"])
            update.update({"status": "sent", "sent_at": utc_now(), "last_error": None})
        except Exception as exc:
            update.update({"status": "failed", "last_error": str(exc)})
        self.db.notification_messages.update_one({"message_id": message["message_id"]}, {"$set": update})

    def _applicant_recipient(self, app: dict, status: str | None = None) -> dict[str, Any] | None:
        applicant_id = app.get("applicant_ref", {}).get("applicant_id")
        if not applicant_id:
            return None
        applicant = self.db.applicants.find_one({"applicant_id": applicant_id})
        if not applicant:
            return None
        preferences = applicant.get("preferences", {}).get("notifications", {})
        if status == "missing_documents" and preferences.get("on_missing_documents") is False:
            return None
        if status == "certificate_issued" and preferences.get("on_certificate_ready") is False:
            return None
        if status not in {None, "missing_documents", "certificate_issued"} and preferences.get("on_status_change") is False:
            return None
        email = applicant.get("contacts", {}).get("email")
        if not email:
            return None
        return {"email": email, "name": applicant.get("full_name"), "applicant_id": applicant_id}
