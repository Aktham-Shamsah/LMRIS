from .applications import router as applications_router
from .parcels import router as parcels_router
from .certificates import router as certificates_router
from .audit_logs import router as audit_logs_router
from .users import router as users_router

__all__ = [
    "applications_router", "parcels_router", "certificates_router",
    "audit_logs_router", "users_router",
]
