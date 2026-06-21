from fastapi import APIRouter, Depends

from app.core.security import require_roles
from app.modules.analytics.service import AnalyticsService
from app.shared.responses import ok

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(require_roles("supervisor", "admin"))])
service = AnalyticsService()


@router.get("/kpis")
def kpis():
    return ok(service.kpis())


@router.get("/applications-by-status")
def applications_by_status():
    return ok(service.applications_by_status())


@router.get("/applications-by-zone")
def applications_by_zone():
    return ok(service.applications_by_zone())


@router.get("/processing-time")
def processing_time():
    return ok(service.processing_time())


@router.get("/surveyors")
def surveyors():
    return ok(service.surveyors())


@router.get("/registrars")
def registrars():
    return ok(service.registrars())


@router.get("/geofeeds/parcels")
def geofeed_parcels(zone_id: str | None = None, status: str | None = None, application_type: str | None = None, dispute_state: str | None = None):
    return ok(service.parcel_geofeed(zone_id, status, application_type, dispute_state))


@router.get("/geofeeds/pending-heatmap")
def pending_heatmap(longitude: float | None = None, latitude: float | None = None):
    return ok(service.pending_heatmap(longitude, latitude))

