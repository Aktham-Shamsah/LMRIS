import pytest
from fastapi import HTTPException

from app.modules.auth.service import authenticate, create_access_token, hash_password, user_from_token, verify_password


def seed_user(db, **overrides):
    user = {
        "email": "registrar@lrmis-demo.ps",
        "full_name": "Demo Registrar",
        "role": "registrar",
        "actor_id": "REG-RM-01",
        "active": True,
        "password_hash": hash_password("registrar123"),
    }
    user.update(overrides)
    db.users.insert_one(user)
    return db.users.find_one({"email": user["email"]})


def test_password_hash_verification():
    stored = hash_password("secret123")
    assert verify_password("secret123", stored)
    assert not verify_password("wrong-secret", stored)


def test_authenticate_success_creates_login_event(db):
    seed_user(db)
    user = authenticate("registrar@lrmis-demo.ps", "registrar123", db)
    assert user["role"] == "registrar"
    assert db.system_events.find_one({"event_type": "auth.login_success"}) is not None


def test_authenticate_rejects_bad_password(db):
    seed_user(db)
    with pytest.raises(HTTPException) as exc:
        authenticate("registrar@lrmis-demo.ps", "bad-password", db)
    assert exc.value.status_code == 401
    assert db.system_events.find_one({"event_type": "auth.login_failed"}) is not None


def test_jwt_round_trip_to_current_user(db):
    user = seed_user(db)
    token = create_access_token(user)
    current = user_from_token(token, db)
    assert current.email == "registrar@lrmis-demo.ps"
    assert current.role == "registrar"
    assert current.actor_id == "REG-RM-01"
