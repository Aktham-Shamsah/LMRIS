from fastapi import HTTPException, status

from app.modules.audit.service import AuditService
from app.modules.survey.models import SurveyMilestoneRequest, SurveyReportCreate
from app.modules.survey.repository import SurveyRepository
from app.shared.enums import SurveyMilestone
from app.shared.ids import next_yearly_id, utc_now


SURVEY_FLOW = [
    SurveyMilestone.ASSIGNED.value,
    SurveyMilestone.VISIT_SCHEDULED.value,
    SurveyMilestone.ARRIVED_ON_SITE.value,
    SurveyMilestone.SURVEY_STARTED.value,
    SurveyMilestone.SURVEY_COMPLETED.value,
    SurveyMilestone.REPORT_UPLOADED.value,
    SurveyMilestone.REGISTRAR_REVIEWED.value,
]

SKILL_BY_APPLICATION_TYPE = {
    "first_registration": "boundary_survey",
    "ownership_transfer": "ownership_review",
    "parcel_subdivision": "parcel_subdivision",
    "parcel_merge": "parcel_merge",
    "boundary_correction": "boundary_survey",
    "certificate_request": "gps_mapping",
}


class SurveyService:
    def __init__(self, repo: SurveyRepository | None = None, audit: AuditService | None = None) -> None:
        self.repo = repo or SurveyRepository()
        self.audit = audit or AuditService()

    def score_surveyor(self, surveyor: dict, application: dict) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        zone_id = application.get("parcel_ref", {}).get("zone_id")
        required_skill = SKILL_BY_APPLICATION_TYPE.get(application.get("application_type"))
        workload = surveyor.get("workload", {})
        active_tasks = workload.get("active_tasks", 0)
        max_tasks = max(workload.get("max_tasks", 1), 1)

        if zone_id in surveyor.get("coverage", {}).get("zone_ids", []):
            score += 40
            reasons.append("zone match")
        if required_skill and required_skill in surveyor.get("skills", []):
            score += 25
            reasons.append("skill match")
        if active_tasks == 0:
            score += 20
            reasons.append("no existing assigned tasks")
        elif active_tasks / max_tasks <= 0.5:
            score += 15
            reasons.append("balanced workload")
        elif active_tasks < max_tasks:
            score += 8
            reasons.append("available capacity")
        if surveyor.get("schedule", {}).get("on_call"):
            score += 10
            reasons.append("available/on call")
        if application.get("priority") in {"high", "urgent"}:
            score += 5
            reasons.append("priority supported")
        return score, reasons

    def auto_assign(self, application_id: str) -> dict:
        application = self.repo.application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found.")
        if application.get("status") != "survey_required":
            raise HTTPException(status_code=409, detail="auto-assign is only allowed when application status is survey_required.")
        if self.repo.existing_task(application_id):
            raise HTTPException(status_code=409, detail="Survey task already exists for this application.")

        zone_id = application.get("parcel_ref", {}).get("zone_id")
        candidates = self.repo.candidates(zone_id)
        if not candidates:
            raise HTTPException(status_code=404, detail="No available surveyor matches zone and workload constraints.")
        ranked = []
        for candidate in candidates:
            score, reasons = self.score_surveyor(candidate, application)
            ranked.append((score, candidate.get("workload", {}).get("active_tasks", 0), candidate, reasons))
        ranked.sort(key=lambda item: (-item[0], item[1], item[2].get("staff_code", "")))
        score, _, surveyor, reasons = ranked[0]
        now = utc_now()
        task_id = next_yearly_id(self.repo.db, "survey_tasks", "task_id", "SURV")
        task = {
            "task_id": task_id,
            "application_id": application_id,
            "parcel_id": application.get("parcel_ref", {}).get("parcel_id"),
            "assigned_surveyor_id": surveyor["staff_code"],
            "status": SurveyMilestone.ASSIGNED.value,
            "milestones": [
                {
                    "type": SurveyMilestone.ASSIGNED.value,
                    "at": now,
                    "by": "system",
                    "meta": {"reason": ", ".join(reasons), "score": score},
                }
            ],
            "field_notes": [],
            "report_uploaded": False,
            "created_at": now,
            "updated_at": now,
        }
        saved = self.repo.create_task(task, surveyor["staff_code"])
        self.audit.record(application_id, "survey_assigned", "system", "assignment_engine", {"surveyor": surveyor["staff_code"], "task_id": task_id, "score": score})
        return saved

    def add_milestone(self, application_id: str, payload: SurveyMilestoneRequest) -> dict:
        application = self.repo.application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found.")
        if application.get("status") not in {"survey_required", "surveyed"}:
            raise HTTPException(status_code=409, detail="Survey milestones cannot bypass the application workflow.")
        task = self.repo.existing_task(application_id)
        if not task:
            raise HTTPException(status_code=404, detail="Survey task not found.")
        current = task["status"]
        requested = payload.milestone.value
        if requested == SurveyMilestone.REPORT_UPLOADED.value:
            raise HTTPException(status_code=409, detail="Use POST /applications/{application_id}/survey-report to upload the report metadata.")
        self._assert_next(current, requested)
        now = utc_now()
        milestone = {"type": requested, "at": now, "by": payload.by, "meta": payload.meta}
        updated = self.repo.update_task_milestone(application_id, milestone)
        self.audit.record(application_id, f"survey_{requested}", "surveyor", payload.by, payload.meta)
        return updated

    def upload_report(self, application_id: str, payload: SurveyReportCreate) -> dict:
        task = self.repo.existing_task(application_id)
        if not task:
            raise HTTPException(status_code=404, detail="Survey task not found.")
        if task["status"] != SurveyMilestone.SURVEY_COMPLETED.value:
            raise HTTPException(status_code=409, detail="Survey report can only be uploaded after survey_completed.")
        now = utc_now()
        report = payload.model_dump(mode="json")
        report.update({"report_id": f"RPT-{task['task_id']}", "application_id": application_id, "uploaded_at": now})
        saved = self.repo.save_report(report)
        self.repo.update_task_milestone(application_id, {"type": SurveyMilestone.REPORT_UPLOADED.value, "at": now, "by": payload.surveyor_id, "meta": {"report_id": report["report_id"]}})
        self.repo.set_application_status(application_id, "surveyed", now)
        self.audit.record(application_id, "survey_report_uploaded", "surveyor", payload.surveyor_id, {"report_id": report["report_id"]})
        self.audit.record(application_id, "status_changed", "system", "survey_workflow", {"from": "survey_required", "to": "surveyed"})
        return saved

    def list_tasks(self, surveyor_id: str | None = None) -> list[dict]:
        return self.repo.tasks(surveyor_id)

    def _assert_next(self, current: str, requested: str) -> None:
        try:
            current_index = SURVEY_FLOW.index(current)
            requested_index = SURVEY_FLOW.index(requested)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unknown survey workflow state.") from exc
        if requested_index != current_index + 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid survey milestone transition from {current} to {requested}.")

