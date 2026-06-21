from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.models import CurrentUser
from app.modules.auth.service import user_from_token

bearer_scheme = HTTPBearer(auto_error=False)

ALL_ROLES = {"applicant", "surveyor", "registrar", "supervisor", "admin"}
STAFF_ROLES = {"surveyor", "registrar", "supervisor", "admin"}
REGISTRAR_ROLES = {"registrar", "supervisor", "admin"}
SUPERVISOR_ROLES = {"supervisor", "admin"}


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    user = user_from_token(credentials.credentials)
    request.state.current_user = user
    return user


def require_roles(*roles: str) -> Callable:
    allowed = {role.lower() for role in roles}

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires one of: {', '.join(sorted(allowed))}.")
        return user

    return dependency


def require_staff_role(user: CurrentUser = Depends(require_roles(*STAFF_ROLES))) -> CurrentUser:
    return user


def require_registrar_role(user: CurrentUser = Depends(require_roles(*REGISTRAR_ROLES))) -> CurrentUser:
    return user


def require_supervisor_role(user: CurrentUser = Depends(require_roles(*SUPERVISOR_ROLES))) -> CurrentUser:
    return user

