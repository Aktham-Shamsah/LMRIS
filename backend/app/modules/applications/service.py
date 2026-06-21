from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status

from app.modules.applicants.repository import ApplicantRepository
from app.modules.applications.models import (
    ApplicationCreate,
    ApplicationStatus,
    CommentCreate,
    DocumentCreate,
    ObjectionCreate,
    ReasonRequest,
    TransitionRequest,
)
from app.modules.applications.repository import ApplicationRepository
from app.modules.audit.service import AuditService
from app.shared.enums import ApplicationType
from app.shared.ids import next_yearly_id, utc_now


TRANSITIONS = {
    "submitted": {"pre_checked", "missing_documents", "on_hold", "rejected"},
    "pre_checked": {"survey_required", "legal_review", "missing_documents", "on_hold", "rejected"},
    "survey_required": {"surveyed", "missing_documents", "on_hold", "rejected"},
    "surveyed": {"legal_review", "missing_documents", "on_hold", "rejected"},
    "legal_review": {"approved", "under_objection", "missing_documents", "on_hold", "rejected"},
    "under_objection": {"legal_review", "on_hold", "rejected"},
    "approved": {"certificate_issued", "on_hold"},
    "certificate_issued": {"closed"},
    "closed": set(),
    "rejected": set(),
    "on_hold": {"rejected"},
    "missing_documents": {"rejected"},
}

SURVEY_REQUIRED_TYPES = {
    ApplicationType.FIRST_REGISTRATION.value,
    ApplicationType.PARCEL_SUBDIVISION.value,
    ApplicationType.PARCEL_MERGE.value,
    ApplicationType.BOUNDARY_CORRECTION.value,
}


class ApplicationService:
    def __init__(
        self,
        repo: ApplicationRepository | None = None,
        applicant_repo: ApplicantRepository | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self.repo = repo or ApplicationRepository()
        self.applicant_repo = applicant_repo or ApplicantRepository(self.repo.db)
        self.audit = audit or AuditService()

    def _parcel_code(self, parcel_ref: dict) -> str:
        if parcel_ref.get("parcel_code"):
            return parcel_ref["parcel_code"]
        zone = parcel_ref["zone_id"].replace("ZONE-", "").replace("-0", "-Z0")
        zone = zone.replace("RM-", "RM-")
        return f"{zone}-B{parcel_ref['block_number']}-P{parcel_ref['parcel_number']}"

    def create(self, payload: ApplicationCreate, idempotency_key: str | None = None) -> dict:
        key = idempotency_key or payload.idempotency_key
        if key:
            existing = self.repo.get_by_idempotency_key(key)
            if existing:
                return existing

        now = utc_now()
        parcel_ref = payload.parcel_ref.model_dump(mode="json")
        parcel_ref["parcel_code"] = self._parcel_code(parcel_ref)
        if parcel_ref.get("geometry"):
            parcel = {
                "parcel_code": parcel_ref["parcel_code"],
                "parcel_number": parcel_ref["parcel_number"],
                "block_number": parcel_ref["block_number"],
                "basin_number": parcel_ref["basin_number"],
                "zone_id": parcel_ref["zone_id"],
                "current_owner_refs": parcel_ref.get("owner_refs", []),
                "geometry": parcel_ref["geometry"],
                "registration_status": "pending_application",
                "dispute_state": "none",
                "created_at": now,
                "updated_at": now,
            }
            saved_parcel = self.repo.upsert_parcel(parcel)
            parcel_ref["parcel_id"] = saved_parcel.get("_id")

        required_documents = [doc.model_dump(mode="json") for doc in payload.required_documents]
        if not required_documents:
            required_documents = [
                {"document_type": "ownership_deed", "required": True, "status": "missing"},
                {"document_type": "id_copy", "required": True, "status": "missing"},
            ]
            if payload.application_type.value == "ownership_transfer":
                required_documents.append({"document_type": "sale_contract", "required": True, "status": "missing"})

        application_id = next_yearly_id(self.repo.db, "land_applications", "application_id", "LRMIS")
        doc = {
            "application_id": application_id,
            "application_type": payload.application_type.value,
            "status": "submitted",
            "priority": payload.priority,
            "applicant_ref": payload.applicant_ref.model_dump(mode="json"),
            "parcel_ref": parcel_ref,
            "description": payload.description,
            "tags": payload.tags,
            "workflow": {
                "current_state": "submitted",
                "allowed_next": sorted(TRANSITIONS["submitted"]),
                "transition_rules_version": "v1.0",
            },
            "required_documents": required_documents,
            "documents": [],
            "comments": [],
            "timestamps": {
                "submitted_at": now,
                "pre_checked_at": None,
                "survey_required_at": None,
                "surveyed_at": None,
                "legal_review_at": None,
                "approved_at": None,
                "certificate_issued_at": None,
                "closed_at": None,
                "updated_at": now,
            },
            "assignment": {
                "assigned_surveyor_id": None,
                "assigned_registrar_id": None,
                "assignment_policy": None,
            },
            "objection": {"has_objection": False, "objection_ids": []},
            "legal_review": {"completed": False, "decision": None, "notes": None},
            "internal": {"notes": [], "visibility": "staff_only"},
            "idempotency_key": key,
        }
        created = self.repo.create(doc)
        self.applicant_repo.add_application(payload.applicant_ref.applicant_id, application_id)
        self.audit.record(application_id, "submitted", "applicant", payload.applicant_ref.applicant_id, {"channel": "web"})
        return created

    def list(self, **kwargs) -> tuple[list[dict], int]:
        return self.repo.list(**kwargs)

    def get(self, application_id: str) -> dict:
        app = self.repo.get(application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        app["allowed_next"] = self.allowed_next(app)
        app["documents_full"] = self.repo.get_documents(app["application_id"])
        app["objections"] = self.repo.get_objections(app["application_id"])
        app["certificate"] = self.repo.latest_certificate(app["application_id"])
        return app

    def allowed_next(self, app: dict) -> list[str]:
        current = app["status"]
        if current in {"on_hold", "missing_documents"}:
            previous = app.get("previous_status")
            allowed = {"rejected"}
            if previous:
                allowed.add(previous)
            return sorted(allowed)
        allowed = set(TRANSITIONS.get(current, set()))
        if current == "pre_checked":
            if app["application_type"] in SURVEY_REQUIRED_TYPES:
                allowed.discard("legal_review")
            else:
                allowed.discard("survey_required")
        return sorted(allowed)

    def transition(self, application_id: str, payload: TransitionRequest) -> dict:
        app = self.get(application_id)
        try:
            target = payload.selected_status.value
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        self._validate_transition(app, target, payload.reason)
        return self._apply_status(app, target, payload.reason, payload.performed_by)

    def hold(self, application_id: str, payload: ReasonRequest) -> dict:
        app = self.get(application_id)
        self._validate_transition(app, "on_hold", payload.reason)
        return self._apply_status(app, "on_hold", payload.reason, payload.performed_by)

    def reject(self, application_id: str, payload: ReasonRequest) -> dict:
        app = self.get(application_id)
        self._validate_transition(app, "rejected", payload.reason)
        return self._apply_status(app, "rejected", payload.reason, payload.performed_by)

    def issue_certificate(self, application_id: str, performed_by: str = "registrar") -> dict:
        app = self.get(application_id)
        if app["status"] != "approved":
            raise HTTPException(status_code=409, detail="Cannot issue certificate unless application is approved.")
        now = utc_now()
        certificate_id = next_yearly_id(self.repo.db, "certificates", "certificate_id", "CERT")
        cert = {
            "certificate_id": certificate_id,
            "application_id": app["application_id"],
            "parcel_id": app.get("parcel_ref", {}).get("parcel_id"),
            "parcel_ref": app.get("parcel_ref"),
            "certificate_type": "ownership_certificate",
            "status": "issued",
            "issued_to": {"applicant_id": app["applicant_ref"]["applicant_id"]},
            "issued_at": now,
            "issued_by": performed_by,
            "verification": {
                "qr_code_url": f"/certificates/{certificate_id}/verify",
                "digital_signature_stub": f"signed-{certificate_id.lower()}",
            },
        }
        saved = self.repo.save_certificate(cert)
        self._apply_status(app, "certificate_issued", None, performed_by)
        self.audit.record(app["application_id"], "certificate_generated", "registrar", performed_by, {"certificate_id": certificate_id})
        return saved

    def add_document(self, application_id: str, payload: DocumentCreate) -> dict:
        app = self.get(application_id)
        now = utc_now()
        document = payload.model_dump(mode="json")
        document.update(
            {
                "document_id": uuid.uuid4().hex,
                "application_id": app["application_id"],
                "uploaded_at": now,
                "reviewed_at": None,
                "reviewed_by": None,
            }
        )
        saved = self.repo.add_document(app["application_id"], document)
        self.audit.record(app["application_id"], "document_uploaded", "applicant", payload.uploaded_by, {"document_type": payload.document_type})
        return saved

    def add_comment(self, application_id: str, payload: CommentCreate) -> dict:
        app = self.get(application_id)
        comment = payload.model_dump(mode="json")
        comment.update({"comment_id": uuid.uuid4().hex, "created_at": utc_now()})
        saved = self.repo.add_comment(app["application_id"], comment)
        self.audit.record(app["application_id"], "comment_added", payload.author_type, payload.author_id)
        return saved

    def add_objection(self, application_id: str, payload: ObjectionCreate) -> dict:
        app = self.get(application_id)
        objection = payload.model_dump(mode="json")
        objection.update(
            {
                "objection_id": uuid.uuid4().hex,
                "application_id": app["application_id"],
                "status": "open",
                "submitted_at": utc_now(),
            }
        )
        saved = self.repo.add_objection(app["application_id"], objection)
        self.audit.record(app["application_id"], "objection_submitted", "applicant", payload.submitted_by, {"reason": payload.reason})
        self.audit.record(app["application_id"], "status_changed", "system", "workflow", {"from": app["status"], "to": "under_objection"})
        return saved

    def timeline(self, application_id: str) -> list[dict]:
        app = self.get(application_id)
        return self.audit.timeline(app["application_id"])

    def _validate_transition(self, app: dict, target: str, reason: str | None) -> None:
        current = app["status"]
        allowed = self.allowed_next(app)
        if target not in allowed:
            raise HTTPException(status_code=409, detail=f"Cannot transition from {current} to {target}. Allowed: {allowed}.")
        if target in {"rejected", "on_hold", "missing_documents", "under_objection"} and not reason:
            raise HTTPException(status_code=422, detail=f"{target} requires a reason.")
        if target == "pre_checked":
            self._require_complete_applicant_and_parcel(app)
        if target == "survey_required" and not self._has_valid_geojson(app):
            raise HTTPException(status_code=422, detail="Cannot move to survey_required unless parcel location is valid GeoJSON.")
        if target == "surveyed" and not self.repo.has_survey_report(app["application_id"]):
            raise HTTPException(status_code=422, detail="Cannot move to surveyed unless survey report exists.")
        if target == "legal_review" and not self.repo.has_ownership_documents(app["application_id"]):
            raise HTTPException(status_code=422, detail="Cannot move to legal_review unless ownership documents are uploaded.")
        if target == "approved":
            if app.get("objection", {}).get("has_objection"):
                open_objections = [o for o in self.repo.get_objections(app["application_id"]) if o.get("status") == "open"]
                if open_objections:
                    raise HTTPException(status_code=422, detail="Cannot approve applications with unresolved objections.")
            if not app.get("legal_review", {}).get("completed"):
                raise HTTPException(status_code=422, detail="Cannot move to approved unless legal review is completed.")

    def _apply_status(self, app: dict, target: str, reason: str | None, performed_by: str) -> dict:
        now = utc_now()
        update: dict[str, Any] = {
            "status": target,
            "workflow.current_state": target,
            "workflow.allowed_next": sorted(TRANSITIONS.get(target, set())),
            "timestamps.updated_at": now,
        }
        timestamp_field = f"timestamps.{target}_at"
        if target in {
            "pre_checked",
            "survey_required",
            "surveyed",
            "legal_review",
            "approved",
            "certificate_issued",
            "closed",
        }:
            update[timestamp_field] = now
        if target in {"on_hold", "missing_documents"}:
            update["previous_status"] = app["status"]
        elif app["status"] in {"on_hold", "missing_documents"}:
            update["previous_status"] = None
        if target == "rejected":
            update["rejection_reason"] = reason
        if target == "on_hold":
            update["hold_reason"] = reason
        if target == "missing_documents":
            update["missing_documents_reason"] = reason
        if target == "under_objection":
            update["objection.has_objection"] = True
        push = None
        if target in {"on_hold", "rejected"}:
            push = {f"{target}_history": {"reason": reason, "by": performed_by, "at": now}}
        updated = self.repo.update(app["application_id"], update, push)
        self.audit.record(app["application_id"], "status_changed", "staff", performed_by, {"from": app["status"], "to": target, "reason": reason})
        return updated

    def _require_complete_applicant_and_parcel(self, app: dict) -> None:
        applicant_ref = app.get("applicant_ref") or {}
        parcel_ref = app.get("parcel_ref") or {}
        missing = []
        for field in ("applicant_id", "applicant_type"):
            if not applicant_ref.get(field):
                missing.append(f"applicant_ref.{field}")
        for field in ("parcel_number", "block_number", "basin_number", "zone_id"):
            if not parcel_ref.get(field):
                missing.append(f"parcel_ref.{field}")
        if missing:
            raise HTTPException(status_code=422, detail=f"Applicant and parcel information are incomplete: {', '.join(missing)}.")

    def _has_valid_geojson(self, app: dict) -> bool:
        geometry = (app.get("parcel_ref") or {}).get("geometry")
        if not geometry:
            parcel_code = (app.get("parcel_ref") or {}).get("parcel_code")
            parcel = self.repo.db.parcels.find_one({"parcel_code": parcel_code}) if parcel_code else None
            geometry = parcel.get("geometry") if parcel else None
        return isinstance(geometry, dict) and geometry.get("type") in {"Point", "Polygon", "MultiPolygon"} and bool(geometry.get("coordinates"))
