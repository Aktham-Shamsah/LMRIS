from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.indexes import create_indexes
from app.db.mongo import close_mongo, get_db
from app.modules.analytics.router import router as analytics_router
from app.modules.applicants.router import router as applicants_router
from app.modules.applications.router import router as applications_router
from app.modules.certificates.router import router as certificates_router
from app.modules.registrar.router import router as registrar_router
from app.modules.staff.router import router as staff_router
from app.modules.survey.router import router as survey_router
from app.shared.errors import register_error_handlers

settings = get_settings()

app = FastAPI(
    title="LRMIS API",
    description="COMP4382 Land Registration Management Information System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


@app.on_event("startup")
def on_startup() -> None:
    create_indexes(get_db())


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_mongo()


@app.get("/health", tags=["System"])
def health():
    return {"success": True, "message": "LRMIS API is running.", "data": {"environment": settings.environment}, "errors": []}


app.include_router(applications_router)
app.include_router(applicants_router)
app.include_router(staff_router)
app.include_router(survey_router)
app.include_router(registrar_router)
app.include_router(certificates_router)
app.include_router(analytics_router)

