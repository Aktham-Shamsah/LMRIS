from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.security import require_roles
from app.modules.auth.models import CurrentUser
from app.modules.survey.models import SurveyMilestoneRequest, SurveyReportCreate
from app.modules.survey.service import SurveyService
from app.shared.responses import ok

router = APIRouter(tags=["Survey"])
service = SurveyService()


@router.post("/applications/{application_id}/auto-assign-surveyor", status_code=201)
def auto_assign_surveyor(application_id: str, _user=Depends(require_roles("registrar", "supervisor", "admin"))):
    return ok(service.auto_assign(application_id), "Surveyor assigned.")


@router.patch("/applications/{application_id}/survey-milestone")
def add_survey_milestone(application_id: str, payload: SurveyMilestoneRequest, user: CurrentUser = Depends(require_roles("surveyor", "supervisor", "admin"))):
    _assert_assigned_surveyor(application_id, user)
    if payload.by == "surveyor":
        payload.by = user.actor_id or user.email
    return ok(service.add_milestone(application_id, payload), "Survey milestone recorded.")


@router.post("/applications/{application_id}/survey-report", status_code=201)
def upload_survey_report(application_id: str, payload: SurveyReportCreate, user: CurrentUser = Depends(require_roles("surveyor", "supervisor", "admin"))):
    _assert_assigned_surveyor(application_id, user)
    if user.role == "surveyor":
        payload.surveyor_id = user.actor_id or payload.surveyor_id
    return ok(service.upload_report(application_id, payload), "Survey report uploaded.")


@router.post("/applications/{application_id}/survey-report/upload", status_code=201)
def upload_survey_report_pdf(
    application_id: str,
    report_title: str = Form(...),
    findings: str = Form(...),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_roles("surveyor", "supervisor", "admin")),
):
    _assert_assigned_surveyor(application_id, user)
    payload = SurveyReportCreate(
        report_title=report_title,
        surveyor_id=user.actor_id or user.email,
        findings=findings,
        field_notes=[],
    )
    return ok(service.upload_report_pdf(application_id, payload, file), "Survey report PDF uploaded.")


@router.get("/survey/tasks")
def list_survey_tasks(surveyor_id: str | None = None, user: CurrentUser = Depends(require_roles("surveyor", "supervisor", "admin"))):
    if user.role == "surveyor":
        surveyor_id = user.actor_id
    return ok({"items": service.list_tasks(surveyor_id)})


def _assert_assigned_surveyor(application_id: str, user: CurrentUser) -> None:
    if user.role != "surveyor":
        return
    task = service.task(application_id)
    if not task or task.get("assigned_surveyor_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Surveyors can only update their assigned survey tasks.")

