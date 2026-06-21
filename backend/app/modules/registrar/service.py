from fastapi import HTTPException

from app.modules.audit.service import AuditService
from app.modules.registrar.models import RegistrarReviewRequest
from app.modules.registrar.repository import RegistrarRepository
from app.shared.ids import utc_now


class RegistrarService:
    def __init__(self, repo: RegistrarRepository | None = None, audit: AuditService | None = None) -> None:
        self.repo = repo or RegistrarRepository()
        self.audit = audit or AuditService()

    def review(self, application_id: str, payload: RegistrarReviewRequest) -> dict:
        app = self.repo.application(application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found.")
        now = utc_now()
        decision = payload.decision

        if decision == "accept":
            return self._accept_survey_report(app, payload, now)
        if decision == "approve":
            return self._approve_legal_review(app, payload, now)
        if decision == "continue_after_objection":
            self.repo.resolve_objections(application_id, now)
            return self._set_status(app, "legal_review", payload, now, {"objection.has_objection": False})
        if decision == "hold":
            if not payload.reason:
                raise HTTPException(status_code=422, detail="Hold decision requires a reason.")
            return self._set_status(app, "on_hold", payload, now, {"previous_status": app["status"], "hold_reason": payload.reason})
        if decision == "reject":
            if not payload.reason:
                raise HTTPException(status_code=422, detail="Reject decision requires a reason.")
            return self._set_status(app, "rejected", payload, now, {"rejection_reason": payload.reason})
        if decision == "request_documents":
            if not payload.reason:
                raise HTTPException(status_code=422, detail="Missing documents decision requires a reason.")
            return self._set_status(app, "missing_documents", payload, now, {"previous_status": app["status"], "missing_documents_reason": payload.reason})
        raise HTTPException(status_code=422, detail="Unsupported registrar decision.")

    def _accept_survey_report(self, app: dict, payload: RegistrarReviewRequest, now) -> dict:
        if app["status"] != "surveyed":
            raise HTTPException(status_code=409, detail="Registrar survey acceptance requires application status surveyed.")
        task = self.repo.survey_task(app["application_id"])
        if not task or task.get("status") != "report_uploaded":
            raise HTTPException(status_code=409, detail="Registrar review requires report_uploaded survey task status.")
        self.repo.mark_survey_registrar_reviewed(
            app["application_id"],
            {"type": "registrar_reviewed", "at": now, "by": payload.registrar_id, "meta": {"decision": payload.decision, "notes": payload.notes}},
        )
        return self._set_status(app, "legal_review", payload, now, {"registrar_review.survey_report_accepted": True})

    def _approve_legal_review(self, app: dict, payload: RegistrarReviewRequest, now) -> dict:
        if app["status"] != "legal_review":
            raise HTTPException(status_code=409, detail="Approval requires application status legal_review.")
        if app.get("objection", {}).get("has_objection"):
            raise HTTPException(status_code=409, detail="Resolve objections before approval.")
        return self._set_status(
            app,
            "approved",
            payload,
            now,
            {
                "legal_review.completed": True,
                "legal_review.decision": "approved",
                "legal_review.notes": payload.notes,
                "legal_review.completed_by": payload.registrar_id,
                "legal_review.completed_at": now,
            },
        )

    def _set_status(self, app: dict, status: str, payload: RegistrarReviewRequest, now, extra: dict | None = None) -> dict:
        update = {
            "status": status,
            "workflow.current_state": status,
            "timestamps.updated_at": now,
            f"timestamps.{status}_at": now,
            "registrar_review.last_decision": payload.decision,
            "registrar_review.last_notes": payload.notes,
            "registrar_review.last_by": payload.registrar_id,
            "registrar_review.last_at": now,
        }
        if extra:
            update.update(extra)
        push = {"internal.notes": {"text": payload.notes or payload.reason or payload.decision, "by": payload.registrar_id, "at": now}}
        updated = self.repo.update_application(app["application_id"], update, push)
        self.audit.record(app["application_id"], "registrar_reviewed", "registrar", payload.registrar_id, {"decision": payload.decision, "from": app["status"], "to": status})
        if app["status"] != status:
            self.audit.record(app["application_id"], "status_changed", "registrar", payload.registrar_id, {"from": app["status"], "to": status})
        return updated

