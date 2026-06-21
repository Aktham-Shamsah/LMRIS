import pytest
from fastapi import HTTPException

from app.modules.registrar.models import RegistrarReviewRequest
from app.modules.survey.models import SurveyMilestoneRequest, SurveyReportCreate
from app.shared.enums import SurveyMilestone


def seed_survey_case(db, status="survey_required"):
    db.land_applications.insert_one(
        {
            "application_id": "LRMIS-2026-0001",
            "application_type": "boundary_correction",
            "status": status,
            "priority": "high",
            "parcel_ref": {"parcel_code": "RM-Z01-B12-P145", "zone_id": "ZONE-RM-01"},
            "timestamps": {},
            "workflow": {"current_state": status},
        }
    )
    db.staff_members.insert_one(
        {
            "staff_code": "SURV-RM-04",
            "name": "Survey Team A",
            "role": "surveyor",
            "active": True,
            "skills": ["boundary_survey"],
            "coverage": {"zone_ids": ["ZONE-RM-01"]},
            "schedule": {"on_call": True},
            "workload": {"active_tasks": 0, "max_tasks": 10},
        }
    )


def test_auto_assignment(db, survey_service):
    seed_survey_case(db)
    task = survey_service.auto_assign("LRMIS-2026-0001")
    assert task["assigned_surveyor_id"] == "SURV-RM-04"
    assert task["status"] == "assigned"


def test_invalid_status_rejection(db, survey_service):
    seed_survey_case(db, status="submitted")
    with pytest.raises(HTTPException):
        survey_service.auto_assign("LRMIS-2026-0001")


def test_milestone_order_and_report_upload(db, survey_service):
    seed_survey_case(db)
    survey_service.auto_assign("LRMIS-2026-0001")
    with pytest.raises(HTTPException):
        survey_service.add_milestone("LRMIS-2026-0001", SurveyMilestoneRequest(milestone=SurveyMilestone.SURVEY_STARTED))
    for milestone in [
        SurveyMilestone.VISIT_SCHEDULED,
        SurveyMilestone.ARRIVED_ON_SITE,
        SurveyMilestone.SURVEY_STARTED,
        SurveyMilestone.SURVEY_COMPLETED,
    ]:
        survey_service.add_milestone("LRMIS-2026-0001", SurveyMilestoneRequest(milestone=milestone, by="SURV-RM-04"))
    report = survey_service.upload_report(
        "LRMIS-2026-0001",
        SurveyReportCreate(report_title="Boundary report", surveyor_id="SURV-RM-04", findings="Valid boundary."),
    )
    assert report["report_id"] == "RPT-SURV-2026-0001"
    assert db.land_applications.find_one({"application_id": "LRMIS-2026-0001"})["status"] == "surveyed"


def test_registrar_review(db, survey_service, registrar_service):
    seed_survey_case(db)
    survey_service.auto_assign("LRMIS-2026-0001")
    for milestone in [
        SurveyMilestone.VISIT_SCHEDULED,
        SurveyMilestone.ARRIVED_ON_SITE,
        SurveyMilestone.SURVEY_STARTED,
        SurveyMilestone.SURVEY_COMPLETED,
    ]:
        survey_service.add_milestone("LRMIS-2026-0001", SurveyMilestoneRequest(milestone=milestone, by="SURV-RM-04"))
    survey_service.upload_report("LRMIS-2026-0001", SurveyReportCreate(report_title="Report", surveyor_id="SURV-RM-04", findings="OK"))
    reviewed = registrar_service.review("LRMIS-2026-0001", RegistrarReviewRequest(decision="accept", registrar_id="REG-RM-01"))
    assert reviewed["status"] == "legal_review"

