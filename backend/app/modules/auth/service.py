from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os
from typing import Any

import jwt
from fastapi import HTTPException, status
from pymongo.database import Database

from app.core.config import get_settings
from app.db.mongo import get_db
from app.modules.auth.models import CurrentUser
from app.shared.serialization import mongo_doc

ROLE_LIMITS = {
    "applicant": "rate_limit_applicant_per_minute",
    "surveyor": "rate_limit_surveyor_per_minute",
    "registrar": "rate_limit_registrar_per_minute",
    "supervisor": "rate_limit_supervisor_per_minute",
    "admin": "rate_limit_admin_per_minute",
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


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": str(user.get("_id") or user.get("user_id") or ""),
        "email": user["email"],
        "full_name": user.get("full_name", user["email"]),
        "role": user["role"],
        "actor_id": user.get("actor_id"),
        "active": user.get("active", True),
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
    record_system_event("auth.login_success", actor=public_user(user), db=database)
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
