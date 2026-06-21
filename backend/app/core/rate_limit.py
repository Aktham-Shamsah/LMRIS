from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock

from fastapi import Request, Response, status
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.modules.auth.service import decode_access_token, record_system_event

Window = deque[float]


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, Window] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


limiter = InMemoryRateLimiter()


async def rate_limit_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    settings = get_settings()
    if not settings.rate_limit_enabled or request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
        return await call_next(request)

    identity = _client_ip(request)
    role = "unauthenticated"
    limit = settings.rate_limit_unauthenticated_per_minute

    if request.url.path == "/auth/login":
        key = f"login:{identity}"
        limit = settings.rate_limit_login_per_minute
    else:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            try:
                payload = decode_access_token(auth_header.split(" ", 1)[1])
                identity = payload.get("sub") or payload.get("email") or identity
                role = payload.get("role", "unauthenticated")
                limit = _role_limit(settings, role)
            except Exception:
                role = "unauthenticated"
        key = f"{role}:{identity}"

    if not limiter.allow(key, limit):
        record_system_event(
            "rate_limit.blocked",
            actor={"identity": identity, "role": role},
            metadata={"path": request.url.path, "limit_per_minute": limit},
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )
    return await call_next(request)


def _role_limit(settings, role: str) -> int:
    return {
        "applicant": settings.rate_limit_applicant_per_minute,
        "surveyor": settings.rate_limit_surveyor_per_minute,
        "registrar": settings.rate_limit_registrar_per_minute,
        "supervisor": settings.rate_limit_supervisor_per_minute,
        "admin": settings.rate_limit_admin_per_minute,
    }.get(role, settings.rate_limit_unauthenticated_per_minute)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"

