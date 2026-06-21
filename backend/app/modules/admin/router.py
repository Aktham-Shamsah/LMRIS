from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.core.security import require_supervisor_role
from app.db.mongo import get_db
from app.modules.auth.models import CurrentUser
from app.modules.notifications.service import NotificationService
from app.shared.serialization import mongo_doc

router = APIRouter(prefix="/admin", tags=["Supervisor Admin"], dependencies=[Depends(require_supervisor_role)])


class TestEmailRequest(BaseModel):
    to: EmailStr | None = None


@router.get("/applicants")
def applicants():
    db = get_db()
    return {"success": True, "data": {"items": [mongo_doc(doc) for doc in db.applicants.find().sort("created_at", -1).limit(100)]}}


@router.get("/applications")
def applications():
    db = get_db()
    return {"success": True, "data": {"items": [mongo_doc(doc) for doc in db.land_applications.find().sort("timestamps.submitted_at", -1).limit(100)]}}


@router.get("/staff")
def staff():
    db = get_db()
    return {"success": True, "data": {"items": [mongo_doc(doc) for doc in db.staff_members.find().sort("staff_code", 1).limit(100)]}}


@router.get("/system-events")
def system_events():
    db = get_db()
    return {"success": True, "data": {"items": [mongo_doc(doc) for doc in db.system_events.find().sort("timestamp", -1).limit(100)]}}


@router.get("/notification-events")
def notification_events():
    db = get_db()
    return {"success": True, "data": {"items": [mongo_doc(doc) for doc in db.notification_events.find().sort("created_at", -1).limit(100)]}}


@router.get("/notification-messages")
def notification_messages():
    db = get_db()
    return {"success": True, "data": {"items": [mongo_doc(doc) for doc in db.notification_messages.find().sort("created_at", -1).limit(100)]}}


@router.post("/test-email", status_code=202)
def test_email(payload: TestEmailRequest, user: CurrentUser = Depends(require_supervisor_role)):
    settings = get_settings()
    recipient = str(payload.to or settings.email_redirect_to or user.email)
    event = NotificationService().send_test_email(recipient)
    return {"success": True, "message": "Test email notification queued.", "data": event}


@router.post("/seed-demo")
def seed_demo():
    from scripts.seed_demo_data import seed

    seed()
    return {"success": True, "message": "Demo data seeded.", "data": {}}


@router.post("/reset-demo")
def reset_demo():
    db = get_db()
    for collection in [
        "applicants",
        "parcels",
        "land_applications",
        "staff_members",
        "application_documents",
        "survey_tasks",
        "survey_reports",
        "objections",
        "certificates",
        "performance_logs",
        "users",
        "system_events",
        "notification_events",
        "notification_messages",
    ]:
        db[collection].delete_many({})
    from scripts.seed_demo_data import seed

    seed()
    return {"success": True, "message": "Demo data reset.", "data": {}}
