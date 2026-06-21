from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from repositories.application_repository import ApplicationRepository
from repositories.parcel_repository import ParcelRepository
from repositories.certificate_repository import CertificateRepository
from repositories.audit_repository import AuditRepository
from models.application import ApplicationModel
from models.certificate import CertificateModel
from schemas.application import (
    ApplicationCreate, ApplicationUpdate,
    StatusTransitionRequest, HoldRequest, RejectRequest, NoteCreate, SurveyReportCreate,
)
from schemas.certificate import CertificateIssueRequest
from services.workflow_service import WorkflowService
from services.audit_service import AuditService
from utils.files import attachment_path, delete_attachment_file, save_attachment, validate_upload


class ApplicationService:
    def __init__(self) -> None:
        self._repo = ApplicationRepository()
        self._parcel_repo = ParcelRepository()
        self._cert_repo = CertificateRepository()
        self._audit_repo = AuditRepository()
        self._workflow = WorkflowService()
        self._audit = AuditService()

    def create(self, payload: ApplicationCreate, performed_by: str = "system") -> dict:
        if payload.idempotency_key:
            existing = self._repo.get_by_idempotency_key(payload.idempotency_key)
            if existing:
                return existing
        doc = ApplicationModel.new(
            application_type=payload.application_type,
            applicant=payload.applicant.model_dump(),
            parcel_ref=payload.parcel_ref.model_dump(),
            notes=payload.notes,
            idempotency_key=payload.idempotency_key,
        )
        created = self._repo.create(doc)
        self._audit.application_created(created["application_id"], payload.application_type, performed_by)
        return created

    def get(self, app_id: str) -> dict:
        app = self._repo.get_by_id(app_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        return app

    def list(
        self,
        skip: int,
        limit: int,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        zone_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict], int]:
        return self._repo.list(
            skip=skip, limit=limit, status=status_filter,
            application_type=type_filter, zone_id=zone_id,
            search=search, sort_by=sort_by, sort_order=sort_order,
        )

    def get_details(self, app_id: str) -> dict:
        app = self.get(app_id)

        parcel_code = app.get("parcel_ref", {}).get("parcel_code")
        parcel = self._parcel_repo.get_by_code(parcel_code) if parcel_code else None

        history_logs, _ = self._audit_repo.list(
            entity_id=app["application_id"], action="status_changed", limit=200
        )
        history = [
            {
                "from_status": log["details"].get("from"),
                "to_status": log["details"].get("to"),
                "performed_by": log["performed_by"],
                "timestamp": log["timestamp"],
            }
            for log in reversed(history_logs)
        ]
        workflow = {
            "current_status": app["status"],
            "allowed_next_statuses": self._workflow.allowed_next(app),
            "previous_status": app.get("previous_status"),
            "hold_reason": app.get("hold_reason"),
            "hold_history": app.get("hold_history", []),
            "rejection_reason": app.get("rejection_reason"),
            "rejection_history": app.get("rejection_history", []),
            "missing_documents_reason": app.get("missing_documents_reason"),
            "objection_reason": app.get("objection_reason"),
            "history": history,
        }

        cert = self._cert_repo.get_latest_by_application_id(app["application_id"])
        certificate = {
            "status": cert["status"] if cert else "not_issued",
            "certificate_id": cert["certificate_id"] if cert else None,
            "issued_at": cert["issued_at"] if cert else None,
            "valid_until": cert["valid_until"] if cert else None,
        }

        return {
            "application": app,
            "workflow": workflow,
            "parcel": parcel,
            "attachments": app.get("documents", []),
            "survey": app.get("survey") or {"status": "not_required"},
            "objections": app.get("objections", []),
            "certificate": certificate,
            "internal_notes": app.get("internal_notes", []),
        }

    def update(self, app_id: str, payload: ApplicationUpdate) -> dict:
        app = self.get(app_id)
        if app["status"] not in ("submitted",):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only submitted (pending-review) applications can be edited.",
            )
        fields = payload.model_dump(exclude_none=True)
        if "applicant" in fields:
            fields["applicant"] = payload.applicant.model_dump()
        if "parcel_ref" in fields:
            fields["parcel_ref"] = payload.parcel_ref.model_dump()
        fields["timestamps.updated_at"] = datetime.now(timezone.utc)
        updated = self._repo.update_fields(app_id, fields)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        return updated

    def transition(self, app_id: str, req: StatusTransitionRequest) -> dict:
        app = self.get(app_id)
        old_status = app["status"]

        self._workflow.validate_transition(app, req.new_status)
        self._workflow.validate_reason(req.new_status, req.reason)
        self._workflow.validate_business_rules(app, req.new_status)

        if req.new_status == "on_hold":
            return self._apply_hold(app, req.reason or "", req.performed_by)

        if req.new_status == "rejected":
            return self._apply_reject(app, req.reason or "", req.performed_by)

        fields = self._workflow.build_update(app, req.new_status, req.reason)
        updated = self._repo.update_fields(app_id, fields)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        # Audit
        self._audit.status_changed(app["application_id"], old_status, req.new_status, req.performed_by)
        if req.new_status == "missing_documents":
            self._audit.missing_documents_flagged(app["application_id"], req.reason or "", req.performed_by)
        if req.new_status == "under_objection":
            self._audit.objection_raised(app["application_id"], req.reason or "", req.performed_by)

        return updated

    def place_on_hold(self, app_id: str, payload: HoldRequest) -> dict:
        """Registrar action: pause processing on an application (User Story - hold)."""
        app = self.get(app_id)
        self._workflow.validate_transition(app, "on_hold")
        self._workflow.validate_business_rules(app, "on_hold")
        return self._apply_hold(app, payload.reason, payload.performed_by)

    def _apply_hold(self, app: dict, reason: str, performed_by: str) -> dict:
        old_status = app["status"]
        fields = self._workflow.build_update(app, "on_hold", reason)
        history_entry = {
            "reason": reason,
            "held_by": performed_by,
            "held_at": fields["timestamps.updated_at"],
        }
        updated = self._repo.place_on_hold(app["id"], fields, history_entry)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        self._audit.status_changed(app["application_id"], old_status, "on_hold", performed_by)
        self._audit.hold_placed(app["application_id"], reason, performed_by)
        return updated

    def reject(self, app_id: str, payload: RejectRequest) -> dict:
        """Registrar action: reject an application (User Story 1.6)."""
        app = self.get(app_id)
        self._workflow.validate_transition(app, "rejected")
        self._workflow.validate_business_rules(app, "rejected")
        return self._apply_reject(app, payload.reason, payload.performed_by)

    def _apply_reject(self, app: dict, reason: str, performed_by: str) -> dict:
        old_status = app["status"]
        fields = self._workflow.build_update(app, "rejected", reason)
        history_entry = {
            "reason": reason,
            "rejected_by": performed_by,
            "rejected_at": fields["timestamps.updated_at"],
        }
        updated = self._repo.reject(app["id"], fields, history_entry)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        self._audit.status_changed(app["application_id"], old_status, "rejected", performed_by)
        self._audit.rejection_issued(app["application_id"], reason, performed_by)
        return updated

    def issue_certificate(self, app_id: str, payload: CertificateIssueRequest) -> dict:
        """Registrar action: generate a certificate for an approved application (User Story 1.7)."""
        app = self.get(app_id)
        self._workflow.validate_transition(app, "certificate_issued")

        parcel_code = app.get("parcel_ref", {}).get("parcel_code")
        if not parcel_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Application has no linked parcel code; cannot issue a certificate.",
            )

        old_status = app["status"]
        cert_doc = CertificateModel.new(
            application_id=app["application_id"],
            parcel_code=parcel_code,
            owner_name=app["applicant"]["name"],
            certificate_type=payload.certificate_type or app["application_type"],
            valid_until=payload.valid_until,
        )
        certificate = self._cert_repo.create(cert_doc)

        fields = self._workflow.build_update(app, "certificate_issued", None)
        updated_app = self._repo.update_fields(app["id"], fields)
        if not updated_app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        self._audit.status_changed(app["application_id"], old_status, "certificate_issued", payload.performed_by)
        self._audit.certificate_generated(certificate["certificate_id"], app["application_id"], payload.performed_by)
        return certificate

    def upload_attachment(self, app_id: str, file: UploadFile, performed_by: str = "system") -> dict:
        self.get(app_id)
        try:
            ext = validate_upload(file)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

        doc_id = uuid.uuid4().hex
        try:
            relative_path, size_bytes = save_attachment(app_id, doc_id, file, ext)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))

        attachment = {
            "doc_id": doc_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": size_bytes,
            "stored_path": relative_path,
            "uploaded_at": datetime.now(timezone.utc),
            "uploaded_by": performed_by,
            "verified": False,
            "verified_at": None,
            "verified_by": None,
        }
        updated = self._repo.add_document(app_id, attachment)
        if not updated:
            delete_attachment_file(relative_path)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        self._audit.attachment_uploaded(updated["application_id"], doc_id, file.filename, performed_by)
        return next(d for d in updated["documents"] if d["doc_id"] == doc_id)

    def list_attachments(self, app_id: str) -> list[dict]:
        app = self.get(app_id)
        return app.get("documents", [])

    def get_attachment_file(self, app_id: str, doc_id: str) -> tuple[Path, str, str]:
        app = self.get(app_id)
        doc = next((d for d in app.get("documents", []) if d["doc_id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
        path = attachment_path(doc["stored_path"])
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file is missing from storage."
            )
        return path, doc["filename"], doc["content_type"]

    def verify_attachment(self, app_id: str, doc_id: str, performed_by: str = "system") -> dict:
        app = self.get(app_id)
        updated = self._repo.verify_document(app_id, doc_id, performed_by)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application or document not found.",
            )
        self._audit.attachment_verified(app["application_id"], doc_id, performed_by)
        return next(d for d in updated["documents"] if d["doc_id"] == doc_id)

    def delete_attachment(self, app_id: str, doc_id: str, performed_by: str = "system") -> None:
        app = self.get(app_id)
        doc = next((d for d in app.get("documents", []) if d["doc_id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

        updated = self._repo.remove_document(app_id, doc_id)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        delete_attachment_file(doc["stored_path"])
        self._audit.attachment_deleted(app["application_id"], doc_id, doc["filename"], performed_by)

    def submit_survey_report(self, app_id: str, payload: SurveyReportCreate) -> dict:
        """Surveyor action: record the field survey report backing a 'surveyed' transition."""
        app = self.get(app_id)
        report = {
            "surveyor_name": payload.surveyor_name,
            "survey_date": payload.survey_date,
            "findings": payload.findings,
            "submitted_by": payload.performed_by,
            "submitted_at": datetime.now(timezone.utc),
        }
        updated = self._repo.set_survey_report(app_id, report)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        self._audit.survey_report_submitted(app["application_id"], payload.performed_by)
        return updated["survey"]["report"]

    def add_note(self, app_id: str, payload: NoteCreate) -> dict:
        """Registrar action: record an internal note/remark (User Story 1.9)."""
        self.get(app_id)
        note = {
            "note_id": uuid.uuid4().hex,
            "text": payload.text,
            "created_by": payload.performed_by,
            "created_at": datetime.now(timezone.utc),
        }
        updated = self._repo.add_note(app_id, note)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        self._audit.note_added(updated["application_id"], note["note_id"], payload.performed_by)
        return next(n for n in updated["internal_notes"] if n["note_id"] == note["note_id"])

    def list_notes(self, app_id: str) -> list[dict]:
        app = self.get(app_id)
        return app.get("internal_notes", [])

    def delete(self, app_id: str) -> None:
        app = self.get(app_id)
        if app["status"] != "submitted":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only submitted (pending-review) applications can be deleted.",
            )
        if not self._repo.delete(app_id):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Delete failed.")
