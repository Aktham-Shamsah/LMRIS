import re
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.core.security import require_roles, require_supervisor_role
from app.db.mongo import get_db
from app.modules.auth.models import CurrentUser, UserRoleUpdateRequest
from app.modules.auth.service import permissions_for_role, public_user, record_system_event
from app.modules.notifications.service import NotificationService
from app.shared.ids import utc_now
from app.shared.serialization import mongo_doc

router = APIRouter(prefix="/admin", tags=["Supervisor Admin"], dependencies=[Depends(require_supervisor_role)])


class TestEmailRequest(BaseModel):
    to: EmailStr | None = None


@router.get("/users")
def users(
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    _user: CurrentUser = Depends(require_roles("admin")),
):
    db = get_db()
    query: dict[str, Any] = {}
    if role:
        query["role"] = role
    if search:
        pattern = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [
            {"email": pattern},
            {"full_name": pattern},
            {"role": pattern},
            {"actor_id": pattern},
        ]
    total = db.users.count_documents(query)
    cursor = db.users.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
    items = []
    for doc in cursor:
        item = public_user(mongo_doc(doc))
        item["created_at"] = mongo_doc(doc).get("created_at")
        item["updated_at"] = mongo_doc(doc).get("updated_at")
        items.append(item)
    return {"success": True, "data": {"items": items, "total": total, "page": page, "limit": limit}}


@router.patch("/users/{user_identifier}/role")
def update_user_role(
    user_identifier: str,
    payload: UserRoleUpdateRequest,
    admin: CurrentUser = Depends(require_roles("admin")),
):
    db = get_db()
    user = _find_user(db, user_identifier)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    role = payload.role
    actor_id = _resolve_actor_id(db, user, role, payload.actor_id)
    update: dict[str, Any] = {"role": role, "actor_id": actor_id, "updated_at": utc_now()}
    if payload.active is not None:
        update["active"] = payload.active
    db.users.update_one({"_id": user["_id"]}, {"$set": update})
    updated = mongo_doc(db.users.find_one({"_id": user["_id"]}))
    record_system_event(
        "admin.user_role_updated",
        actor=admin.model_dump(),
        metadata={
            "target_email": updated["email"],
            "role": role,
            "actor_id": actor_id,
            "permissions": permissions_for_role(role),
        },
        db=db,
    )
    return {"success": True, "message": "User role updated.", "data": public_user(updated)}


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


def _find_user(db, identifier: str) -> dict | None:
    if ObjectId.is_valid(identifier):
        return db.users.find_one({"_id": ObjectId(identifier)})
    return db.users.find_one({"email": identifier.lower()})


def _resolve_actor_id(db, user: dict, role: str, requested_actor_id: str | None) -> str | None:
    if requested_actor_id:
        return requested_actor_id
    current_actor_id = user.get("actor_id")
    if role == "applicant":
        if current_actor_id and str(current_actor_id).startswith("APP-"):
            return current_actor_id
        applicant = db.applicants.find_one({"contacts.email": user["email"]})
        if applicant:
            return applicant["applicant_id"]
        raise HTTPException(status_code=422, detail="Assigning applicant role requires an applicant actor_id.")

    prefix_by_role = {"surveyor": "SURV", "registrar": "REG", "supervisor": "SUP", "admin": "ADM"}
    prefix = prefix_by_role.get(role)
    if not prefix:
        raise HTTPException(status_code=422, detail="Unsupported role.")
    staff = db.staff_members.find_one({"contacts.email": user["email"], "role": role})
    if staff:
        return staff["staff_code"]
    now = utc_now()
    staff_code = f"{prefix}-GEN-{db.staff_members.count_documents({'role': role}) + 1:02d}"
    db.staff_members.insert_one(
        {
            "staff_id": staff_code,
            "staff_code": staff_code,
            "name": user.get("full_name", user["email"]),
            "role": role,
            "department": "Land Registration",
            "skills": [],
            "coverage": {"zone_ids": [], "geo_fence": None},
            "schedule": {"timezone": "Asia/Jerusalem", "shifts": [], "on_call": False},
            "workload": {"active_tasks": 0, "max_tasks": 10},
            "contacts": {"email": user["email"], "phone": None},
            "active": True,
            "created_at": now,
            "updated_at": now,
        }
    )
    return staff_code
