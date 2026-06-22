from app.modules.notifications.service import NotificationService


class FakeEmailSender:
    def __init__(self):
        self.sent = []

    def send(self, *, to_email: str, subject: str, body: str) -> None:
        self.sent.append({"to_email": to_email, "subject": subject, "body": body})


class EmailEnabledSettings:
    email_enabled = True
    email_send_immediately = True


class EmailDisabledSettings:
    email_enabled = False
    email_send_immediately = False


def seed_applicant(db):
    db.applicants.insert_one(
        {
            "applicant_id": "APP-400000000",
            "full_name": "Nour Demo",
            "contacts": {"email": "nour@example.com"},
            "preferences": {
                "notifications": {
                    "on_status_change": True,
                    "on_missing_documents": True,
                    "on_certificate_ready": True,
                }
            },
        }
    )


def test_status_change_queues_email_message(db, monkeypatch):
    monkeypatch.setattr("app.modules.notifications.service.get_settings", lambda: EmailDisabledSettings())
    seed_applicant(db)
    service = NotificationService(db)
    service.application_status_changed(
        {"application_id": "LRMIS-2026-0001", "applicant_ref": {"applicant_id": "APP-400000000"}},
        "submitted",
        "approved",
    )
    event = db.notification_events.find_one({"event_type": "application.status_changed"})
    message = db.notification_messages.find_one({"event_id": event["event_id"]})
    assert message["to_email"] == "nour@example.com"
    assert message["status"] == "queued"


def test_email_sender_runs_when_enabled(db, monkeypatch):
    monkeypatch.setattr("app.modules.notifications.service.get_settings", lambda: EmailEnabledSettings())
    sender = FakeEmailSender()
    service = NotificationService(db, sender)
    service.send_test_email("admin@example.com")
    message = db.notification_messages.find_one({"channel": "email"})
    assert sender.sent[0]["to_email"] == "admin@example.com"
    assert message["status"] == "sent"
