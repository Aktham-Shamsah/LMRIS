from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from services.workflow_service import WorkflowService


class FakeParcelRepository:
    """Stand-in for ParcelRepository so tests don't need a live MongoDB."""

    def __init__(self, found: bool = True):
        self.found = found
        self.lookups: list[str] = []

    def get_by_code(self, parcel_code):
        self.lookups.append(parcel_code)
        return {"parcel_code": parcel_code} if self.found else None


def make_application(**overrides) -> dict:
    base = {
        "status": "submitted",
        "application_type": "first_registration",
        "applicant": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "national_id": "123456789",
            "phone": "",
        },
        "parcel_ref": {
            "parcel_number": "12",
            "block_number": "3",
            "basin_number": "4",
            "zone_id": "Z1",
            "parcel_code": "PC-001",
        },
        "documents": [],
        "objections": [],
        "survey": {"status": "pending", "report": None},
    }
    base.update(overrides)
    return base


# --- Rule 1: pre_checked requires complete applicant + parcel data ---------


def test_pre_checked_blocked_when_applicant_field_missing():
    app = make_application(applicant={"name": "Jane Doe", "email": "", "national_id": "123"})
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    with pytest.raises(HTTPException) as exc:
        svc.validate_business_rules(app, "pre_checked")

    assert exc.value.status_code == 422
    assert "applicant" in exc.value.detail.lower()
    assert "email" in exc.value.detail.lower()


def test_pre_checked_blocked_when_parcel_ref_field_missing():
    app = make_application(
        parcel_ref={
            "parcel_number": "",
            "block_number": "3",
            "basin_number": "4",
            "zone_id": "Z1",
            "parcel_code": "PC-001",
        }
    )
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    with pytest.raises(HTTPException) as exc:
        svc.validate_business_rules(app, "pre_checked")

    assert exc.value.status_code == 422
    assert "parcel information is incomplete" in exc.value.detail.lower()


def test_pre_checked_blocked_when_parcel_record_not_found():
    app = make_application()
    repo = FakeParcelRepository(found=False)
    svc = WorkflowService(parcel_repo=repo)

    with pytest.raises(HTTPException) as exc:
        svc.validate_business_rules(app, "pre_checked")

    assert exc.value.status_code == 422
    assert "no parcel record found" in exc.value.detail.lower()
    assert repo.lookups == ["PC-001"]


def test_pre_checked_blocked_when_parcel_code_missing():
    app = make_application(
        parcel_ref={
            "parcel_number": "12",
            "block_number": "3",
            "basin_number": "4",
            "zone_id": "Z1",
            "parcel_code": "",
        }
    )
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    with pytest.raises(HTTPException) as exc:
        svc.validate_business_rules(app, "pre_checked")

    assert exc.value.status_code == 422
    assert "no parcel record found" in exc.value.detail.lower()


def test_pre_checked_allowed_when_applicant_and_parcel_complete():
    app = make_application()
    svc = WorkflowService(parcel_repo=FakeParcelRepository(found=True))

    svc.validate_business_rules(app, "pre_checked")  # should not raise


# --- Rule 2: surveyed requires an on-file survey report ---------------------


def test_surveyed_blocked_when_no_survey_report():
    app = make_application(status="survey_required", survey={"status": "scheduled", "report": None})
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    with pytest.raises(HTTPException) as exc:
        svc.validate_business_rules(app, "surveyed")

    assert exc.value.status_code == 422
    assert "survey report" in exc.value.detail.lower()


def test_surveyed_blocked_when_survey_key_missing_entirely():
    app = make_application(status="survey_required")
    del app["survey"]
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    with pytest.raises(HTTPException):
        svc.validate_business_rules(app, "surveyed")


def test_surveyed_allowed_when_survey_report_present():
    app = make_application(
        status="survey_required",
        survey={
            "status": "scheduled",
            "report": {
                "surveyor_name": "John Smith",
                "survey_date": datetime.now(timezone.utc),
                "findings": "Boundaries confirmed, no encroachments.",
                "submitted_by": "surveyor1",
                "submitted_at": datetime.now(timezone.utc),
            },
        },
    )
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    svc.validate_business_rules(app, "surveyed")  # should not raise


# --- Regression: unrelated transitions must be unaffected -------------------


def test_unrelated_transition_not_affected_by_new_rules():
    app = make_application(status="legal_review", applicant={}, parcel_ref={}, survey={"status": "completed", "report": None})
    svc = WorkflowService(parcel_repo=FakeParcelRepository())

    svc.validate_business_rules(app, "approved")  # should not raise due to the new rules
