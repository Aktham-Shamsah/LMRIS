from fastapi import Header, HTTPException, status


STAFF_ROLES = {"staff", "surveyor", "registrar", "manager", "admin"}


def require_staff_role(x_lrmss_role: str | None = Header(default=None, alias="X-LRMIS-Role")) -> str:
    role = (x_lrmss_role or "").strip().lower()
    if role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff-only endpoint. Send X-LRMIS-Role as staff, surveyor, registrar, manager, or admin.",
        )
    return role


def require_registrar_role(x_lrmss_role: str | None = Header(default=None, alias="X-LRMIS-Role")) -> str:
    role = (x_lrmss_role or "").strip().lower()
    if role not in {"registrar", "manager", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registrar endpoint. Send X-LRMIS-Role as registrar, manager, or admin.",
        )
    return role

