from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsService


def test_analytics_basic_response(db):
    db.land_applications.insert_many(
        [
            {"application_id": "A1", "status": "submitted", "application_type": "ownership_transfer", "parcel_ref": {"zone_id": "ZONE-RM-01"}},
            {"application_id": "A2", "status": "approved", "application_type": "certificate_request", "parcel_ref": {"zone_id": "ZONE-RM-02"}},
        ]
    )
    service = AnalyticsService(AnalyticsRepository(db))
    kpis = service.kpis()
    by_status = service.applications_by_status()
    assert kpis["total_applications"] == 2
    assert any(item["_id"] == "submitted" for item in by_status)

