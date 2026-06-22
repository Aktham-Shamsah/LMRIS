from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os
import secrets
from typing import Any

import jwt
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError
from pymongo.database import Database

from app.core.config import get_settings
from app.db.mongo import get_db
from app.modules.auth.models import CurrentUser, SignupRequest
from app.modules.notifications.service import NotificationService
from app.shared.serialization import mongo_doc

ROLE_LIMITS = {
    "applicant": "rate_limit_applicant_per_minute",
    "surveyor": "rate_limit_surveyor_per_minute",
    "registrar": "rate_limit_registrar_per_minute",
    "supervisor": "rate_limit_supervisor_per_minute",
    "admin": "rate_limit_admin_per_minute",
}

ROLE_PERMISSIONS = {
    "applicant": [
        "applicants:read_own",
        "applications:create",
        "applications:read_own",
        "documents:upload",
        "comments:create",
        "objections:create",
        "certificates:read_own",
    ],
    "surveyor": [
        "survey_tasks:read_assigned",
        "survey_milestones:update_assigned",
        "survey_reports:upload_assigned",
    ],
    "registrar": [
        "applications:read",
        "applications:transition",
        "documents:upload",
        "registrar_reviews:update",
        "certificates:issue",
        "certificates:read",
    ],
    "supervisor": [
        "applications:read",
        "staff:manage",
        "analytics:read",
        "map:read",
        "notifications:read",
    ],
    "admin": [
        "users:read",
        "users:assign_roles",
        "applications:read",
        "staff:manage",
        "analytics:read",
        "map:read",
        "notifications:read",
        "system:manage",
    ],
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str, *, iterations: int = 120_000) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iteration_text, salt_text, digest_text = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iteration_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def permissions_for_role(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    role = user["role"]
    return {
        "user_id": str(user.get("_id") or user.get("user_id") or ""),
        "email": user["email"],
        "full_name": user.get("full_name", user["email"]),
        "role": role,
        "actor_id": user.get("actor_id"),
        "active": user.get("active", True),
        "email_verified": user.get("email_verified", True),
        "permissions": permissions_for_role(role),
    }


def create_access_token(user: dict[str, Any]) -> str:
    settings = get_settings()
    now = utc_now()
    expires = now + timedelta(minutes=settings.jwt_access_token_minutes)
    payload = {
        "sub": str(user.get("_id") or user.get("user_id")),
        "email": user["email"],
        "role": user["role"],
        "actor_id": user.get("actor_id"),
        "permissions": permissions_for_role(user["role"]),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "typ": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc
    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
    return payload


def get_user_by_email(email: str, db: Database | None = None) -> dict | None:
    database = db if db is not None else get_db()
    return mongo_doc(database.users.find_one({"email": email.lower()}))


def authenticate(email: str, password: str, db: Database | None = None) -> dict:
    database = db if db is not None else get_db()
    user = get_user_by_email(email, database)
    if not user or not user.get("active", True) or not verify_password(password, user.get("password_hash", "")):
        record_system_event(
            "auth.login_failed",
            actor={"email": email.lower()},
            metadata={"reason": "bad_credentials"},
            db=database,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user.get("email_verified", True):
        record_system_event(
            "auth.login_failed",
            actor={"email": email.lower()},
            metadata={"reason": "email_not_verified"},
            db=database,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification is required before login.")
    record_system_event("auth.login_success", actor=public_user(user), db=database)
    return user


def signup(payload: SignupRequest, db: Database | None = None) -> dict:
    database = db if db is not None else get_db()
    email = str(payload.email).lower()
    if database.users.find_one({"email": email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    now = utc_now()
    applicant_id = f"APP-{payload.national_id.strip()}"
    applicant = database.applicants.find_one({"applicant_id": applicant_id})
    if not applicant:
        applicant = {
            "applicant_id": applicant_id,
            "full_name": payload.full_name,
            "applicant_type": payload.applicant_type.value,
            "identity": {
                "national_id": payload.national_id.strip(),
                "verified": False,
                "verification_method": "email_otp",
                "verified_at": None,
            },
            "contacts": {"email": email, "phone": payload.phone},
            "address": {
                "city": payload.city,
                "neighborhood": payload.neighborhood,
                "zone_id": payload.zone_id,
            },
            "verification_state": "unverified",
            "preferences": {
                "preferred_contact": "email",
                "language": payload.preferred_language,
                "notifications": {
                    "on_status_change": True,
                    "on_missing_documents": True,
                    "on_certificate_ready": True,
                },
            },
            "privacy_settings": {"share_contact_with_staff": True, "public_certificate_lookup": False},
            "linked_applications": [],
            "stats": {"total_applications": 0, "approved_applications": 0, "pending_applications": 0},
            "created_at": now,
            "updated_at": now,
        }
        database.applicants.insert_one(applicant)
    else:
        database.applicants.update_one(
            {"applicant_id": applicant_id},
            {
                "$set": {
                    "full_name": payload.full_name,
                    "contacts.email": email,
                    "contacts.phone": payload.phone,
                    "updated_at": now,
                }
            },
        )

    user = {
        "email": email,
        "full_name": payload.full_name,
        "role": "applicant",
        "actor_id": applicant_id,
        "active": True,
        "email_verified": False,
        "password_hash": hash_password(payload.password),
        "created_at": now,
        "updated_at": now,
    }
    try:
        database.users.insert_one(user)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.") from exc

    verification = send_signup_otp(email, database)
    record_system_event("auth.signup_created", actor=public_user(user), db=database)
    return {"user": public_user(user), "verification": verification}


def send_signup_otp(email: str, db: Database | None = None) -> dict:
    database = db if db is not None else get_db()
    normalized_email = email.lower()
    user = mongo_doc(database.users.find_one({"email": normalized_email}))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    if user.get("email_verified", True):
        return {"email": normalized_email, "already_verified": True}

    settings = get_settings()
    now = utc_now()
    expires_at = now + timedelta(minutes=settings.email_otp_minutes)
    code = _generate_otp()
    database.email_verifications.update_many(
        {"email": normalized_email, "purpose": "signup", "consumed_at": None},
        {"$set": {"invalidated_at": now}},
    )
    verification = {
        "verification_id": secrets.token_urlsafe(18),
        "email": normalized_email,
        "purpose": "signup",
        "otp_hash": _otp_digest(code),
        "attempts": 0,
        "created_at": now,
        "expires_at": expires_at,
        "consumed_at": None,
    }
    database.email_verifications.insert_one(verification)
    NotificationService(database).publish(
        event_type="auth.email_verification",
        subject="Your LRMIS email verification code",
        body=(
            f"Hello {user.get('full_name') or 'Applicant'},\n\n"
            f"Your LRMIS email verification code is {code}.\n"
            f"This code expires in {settings.email_otp_minutes} minutes.\n\n"
            "If you did not create an LRMIS account, you can ignore this message."
        ),
        recipients=[{"email": normalized_email, "name": user.get("full_name")}],
        metadata={"purpose": "signup", "expires_at": expires_at.isoformat()},
    )
    record_system_event("auth.signup_otp_sent", actor={"email": normalized_email}, db=database)
    return mongo_doc(
        {
            "email": normalized_email,
            "expires_at": expires_at,
            "verification_required": True,
        }
    )


def verify_signup_otp(email: str, otp_code: str, db: Database | None = None) -> dict:
    database = db if db is not None else get_db()
    normalized_email = email.lower()
    now = utc_now()
    verification = database.email_verifications.find_one(
        {
            "email": normalized_email,
            "purpose": "signup",
            "consumed_at": None,
            "invalidated_at": {"$exists": False},
        },
        sort=[("created_at", -1)],
    )
    if not verification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active verification code was found.")
    expires_at = verification.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Verification code has expired.")
    if verification.get("attempts", 0) >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many verification attempts.")
    if not hmac.compare_digest(verification.get("otp_hash", ""), _otp_digest(otp_code.strip())):
        database.email_verifications.update_one(
            {"verification_id": verification["verification_id"]},
            {"$inc": {"attempts": 1}, "$set": {"last_attempt_at": now}},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")

    database.email_verifications.update_one(
        {"verification_id": verification["verification_id"]},
        {"$set": {"consumed_at": now}},
    )
    database.users.update_one(
        {"email": normalized_email},
        {"$set": {"email_verified": True, "updated_at": now}},
    )
    user = mongo_doc(database.users.find_one({"email": normalized_email}))
    if user and user.get("actor_id"):
        database.applicants.update_one(
            {"applicant_id": user["actor_id"]},
            {
                "$set": {
                    "identity.verified": True,
                    "identity.verification_method": "email_otp",
                    "identity.verified_at": now,
                    "verification_state": "verified",
                    "updated_at": now,
                }
            },
        )
    user = mongo_doc(database.users.find_one({"email": normalized_email}))
    record_system_event("auth.email_verified", actor=public_user(user), db=database)
    return user


def user_from_token(token: str, db: Database | None = None) -> CurrentUser:
    database = db if db is not None else get_db()
    payload = decode_access_token(token)
    user = mongo_doc(database.users.find_one({"email": payload["email"].lower(), "active": True}))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists or is inactive.")
    return CurrentUser(**public_user(user))


def record_system_event(
    event_type: str,
    *,
    actor: dict | None = None,
    metadata: dict | None = None,
    db: Database | None = None,
) -> None:
    database = db if db is not None else get_db()
    database.system_events.insert_one(
        {
            "event_type": event_type,
            "actor": actor or {},
            "metadata": metadata or {},
            "timestamp": utc_now(),
        }
    )


def _generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _otp_digest(code: str) -> str:
    settings = get_settings()
    return hmac.new(settings.jwt_secret_key.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()
