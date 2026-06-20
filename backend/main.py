from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database.indexes import ensure_indexes
from routers import applications_router, parcels_router, certificates_router, audit_logs_router, users_router
from utils.exceptions import register_exception_handlers

settings = get_settings()

DESCRIPTION = """
## Land Registry Web Service API

Built with **FastAPI + PyMongo + MongoDB**.

### Collections
| Collection | Purpose |
|---|---|
| `land_applications` | Application lifecycle management |
| `parcels` | Land parcel registry with geospatial data |
| `certificates` | Issued land ownership certificates |
| `performance_logs` | Audit trail for all important actions |

### Application Types
`first_registration` · `ownership_transfer` · `parcel_subdivision` · `parcel_merge` · `boundary_correction` · `certificate_request`

### Workflow (State Machine)
```
submitted → pre_checked → survey_required → surveyed → legal_review
    → approved → certificate_issued → closed

Alternative states: rejected · on_hold · missing_documents · under_objection
```

### Geospatial
Parcel geometry is stored as **GeoJSON** and indexed with a **2dsphere** index,
enabling `$near` and `$geoWithin` queries.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_indexes()
    except Exception as exc:
        import logging
        logging.warning(f"Could not create indexes on startup (MongoDB may be offline): {exc}")
    yield


app = FastAPI(
    title="Land Registry Web Service",
    description=DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={"name": "Development Team"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

PREFIX = "/api/v1"
app.include_router(applications_router, prefix=PREFIX)
app.include_router(parcels_router, prefix=PREFIX)
app.include_router(certificates_router, prefix=PREFIX)
app.include_router(audit_logs_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)


@app.get("/", tags=["Health"], summary="Root health check")
def root():
    return {"status": "ok", "version": "1.0.0", "docs": "/docs"}


@app.get("/api/v1/health", tags=["Health"], summary="API health check")
def api_health():
    return {"status": "ok", "database": settings.mongo_db_name, "env": settings.app_env}
