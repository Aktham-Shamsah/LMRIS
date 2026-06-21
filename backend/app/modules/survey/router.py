from fastapi import APIRouter, Depends

from app.core.security import require_staff_role
from app.modules.survey.models import SurveyMilestoneRequest, SurveyReportCreate
from app.modules.survey.service import SurveyService
from app.shared.responses import ok

router = APIRouter(tags=["Survey"], dependencies=[Depends(require_staff_role)])
service = SurveyService()


@router.post("/applications/{application_id}/auto-assign-surveyor", status_code=201)
def auto_assign_surveyor(application_id: str):
    return ok(service.auto_assign(application_id), "Surveyor assigned.")


@router.patch("/applications/{application_id}/survey-milestone")
def add_survey_milestone(application_id: str, payload: SurveyMilestoneRequest):
    return ok(service.add_milestone(application_id, payload), "Survey milestone recorded.")


@router.post("/applications/{application_id}/survey-report", status_code=201)
def upload_survey_report(application_id: str, payload: SurveyReportCreate):
    return ok(service.upload_report(application_id, payload), "Survey report uploaded.")


@router.get("/survey/tasks")
def list_survey_tasks(surveyor_id: str | None = None):
    return ok({"items": service.list_tasks(surveyor_id)})

