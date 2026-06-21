from fastapi import APIRouter, Depends

from app.core.security import require_roles
from app.modules.survey.models import SurveyMilestoneRequest, SurveyReportCreate
from app.modules.survey.service import SurveyService
from app.shared.responses import ok

router = APIRouter(tags=["Survey"])
service = SurveyService()


@router.post("/applications/{application_id}/auto-assign-surveyor", status_code=201)
def auto_assign_surveyor(application_id: str, _user=Depends(require_roles("registrar", "supervisor", "admin"))):
    return ok(service.auto_assign(application_id), "Surveyor assigned.")


@router.patch("/applications/{application_id}/survey-milestone")
def add_survey_milestone(application_id: str, payload: SurveyMilestoneRequest, user=Depends(require_roles("surveyor", "supervisor", "admin"))):
    if payload.by == "surveyor":
        payload.by = user.actor_id or user.email
    return ok(service.add_milestone(application_id, payload), "Survey milestone recorded.")


@router.post("/applications/{application_id}/survey-report", status_code=201)
def upload_survey_report(application_id: str, payload: SurveyReportCreate, user=Depends(require_roles("surveyor", "supervisor", "admin"))):
    if user.role == "surveyor":
        payload.surveyor_id = user.actor_id or payload.surveyor_id
    return ok(service.upload_report(application_id, payload), "Survey report uploaded.")


@router.get("/survey/tasks")
def list_survey_tasks(surveyor_id: str | None = None, user=Depends(require_roles("surveyor", "supervisor", "admin"))):
    if user.role == "surveyor":
        surveyor_id = user.actor_id
    return ok({"items": service.list_tasks(surveyor_id)})

