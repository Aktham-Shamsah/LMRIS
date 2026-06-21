import pytest
from fastapi import HTTPException

from app.modules.applications.models import ApplicationCreate, ApplicantRef, DocumentCreate, ParcelRef, TransitionRequest
from app.shared.enums import ApplicantType, ApplicationStatus, ApplicationType


def application_payload(geometry=True):
    geo = {"type": "Polygon", "coordinates": [[[35.2, 31.9], [35.21, 31.9], [35.21, 31.91], [35.2, 31.91], [35.2, 31.9]]]} if geometry else None
    return ApplicationCreate(
        application_type=ApplicationType.BOUNDARY_CORRECTION,
        applicant_ref=ApplicantRef(applicant_id="APP-400000000", applicant_type=ApplicantType.CITIZEN),
        parcel_ref=ParcelRef(parcel_number="145", block_number="12", basin_number="3", zone_id="ZONE-RM-01", geometry=geo),
        idempotency_key="same-key",
    )


def test_idempotent_application_creation(application_service):
    first = application_service.create(application_payload())
    second = application_service.create(application_payload())
    assert first["application_id"] == second["application_id"]


def test_workflow_rejects_survey_without_geojson(application_service):
    app = application_service.create(application_payload(geometry=False), idempotency_key="no-geo")
    application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.PRE_CHECKED))
    with pytest.raises(HTTPException) as exc:
        application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.SURVEY_REQUIRED))
    assert exc.value.status_code == 422


def test_legal_review_requires_ownership_document(application_service):
    app = application_service.create(application_payload(), idempotency_key="legal-doc")
    application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.PRE_CHECKED))
    application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.SURVEY_REQUIRED))
    application_service.repo.db.survey_reports.insert_one({"application_id": app["application_id"], "report_id": "RPT-1"})
    application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.SURVEYED))
    with pytest.raises(HTTPException):
        application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.LEGAL_REVIEW))
    application_service.add_document(app["application_id"], DocumentCreate(document_type="ownership_deed", filename="deed.pdf", is_ownership_doc=True))
    moved = application_service.transition(app["application_id"], TransitionRequest(target_status=ApplicationStatus.LEGAL_REVIEW))
    assert moved["status"] == "legal_review"


def test_certificate_requires_approved(application_service):
    app = application_service.create(application_payload(), idempotency_key="cert")
    with pytest.raises(HTTPException):
        application_service.issue_certificate(app["application_id"])

