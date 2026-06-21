from __future__ import annotations
from datetime import datetime, timezone
from fastapi import HTTPException, status
from models.application import ApplicationModel
from repositories.parcel_repository import ParcelRepository

# Static next-state graph for the main flow. Pause states (on_hold,
# missing_documents) are not listed as sources here: their allowed next
# state is computed dynamically from `previous_status` in allowed_next().
TRANSITIONS: dict[str, set[str]] = {
    "submitted":          {"pre_checked", "missing_documents", "on_hold", "rejected"},
    "pre_checked":        {"survey_required", "legal_review", "missing_documents", "on_hold", "rejected"},
    "survey_required":    {"surveyed", "missing_documents", "on_hold", "rejected"},
    "surveyed":           {"legal_review", "missing_documents", "on_hold", "rejected"},
    "legal_review":       {"approved", "under_objection", "missing_documents", "on_hold", "rejected"},
    "under_objection":    {"legal_review", "rejected"},
    "approved":           {"certificate_issued", "on_hold"},
    "certificate_issued": {"closed"},
    "closed":             set(),
    "rejected":           set(),
}

# Pause states that must resume back to the exact status they were entered from.
RESUMABLE_STATUSES: set[str] = {"on_hold", "missing_documents"}

# Statuses that require a `reason` to be provided.
REASON_REQUIRED: set[str] = {"on_hold", "rejected", "missing_documents", "under_objection"}

# Applicant fields that must be present before pre-check can complete.
REQUIRED_APPLICANT_FIELDS: tuple[str, ...] = ("name", "email", "national_id")

# Parcel reference fields that must be present before pre-check can complete.
REQUIRED_PARCEL_REF_FIELDS: tuple[str, ...] = ("parcel_number", "block_number", "basin_number", "zone_id")


class WorkflowService:
    """State machine for land application workflow transitions (User Story 1.4)."""

    def __init__(self, parcel_repo: ParcelRepository | None = None) -> None:
        self._parcel_repo = parcel_repo or ParcelRepository()

    def allowed_next(self, application: dict) -> list[str]:
        current = application["status"]

        if current in RESUMABLE_STATUSES:
            options = {"rejected"}
            previous = application.get("previous_status")
            if previous:
                options.add(previous)
            return sorted(options)

        allowed = set(TRANSITIONS.get(current, set()))

        if current == "pre_checked":
            # The survey stage only applies to application types that require
            # a field survey; other types skip straight to legal review.
            if application.get("application_type") in ApplicationModel.SURVEY_REQUIRED_TYPES:
                allowed.discard("legal_review")
            else:
                allowed.discard("survey_required")

        return sorted(allowed)

    def validate_transition(self, application: dict, target: str) -> None:
        current = application["status"]
        allowed = self.allowed_next(application)
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot transition from '{current}' to '{target}'. "
                    f"Allowed next states: {allowed or 'none (terminal state)'}."
                ),
            )

    def validate_reason(self, target: str, reason: str | None) -> None:
        if target in REASON_REQUIRED and not reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"A reason is required when transitioning to '{target}'.",
            )

    def validate_business_rules(self, application: dict, target: str) -> None:
        """Domain rules beyond plain graph adjacency."""
        current = application["status"]
        documents = application.get("documents", [])
        objections = application.get("objections", [])
        open_objections = [o for o in objections if o.get("status") == "open"]

        if target == "pre_checked":
            self._validate_pre_check_completeness(application)
        if target == "survey_required":
            parcel = application.get("parcel")

            if not parcel or not parcel.get("location") or not parcel.get("location").get("coordinates"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot move to survey_required without a valid parcel location.",
                )
        if target == "surveyed":
            self._validate_survey_report_exists(application)

        if current == "pre_checked" and target in ("survey_required", "legal_review"):
            if documents and any(not d.get("verified") for d in documents):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="All uploaded documents must be verified before completing the pre-check stage.",
                )

        if target == "approved" and open_objections:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot approve an application with unresolved objections.",
            )
        if target == "legal_review":
            attachments = application.get("attachments", [])

            ownership_docs = [
                a for a in attachments
                if a.get("is_ownership_doc") is True
            ]

            if len(ownership_docs) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Ownership documents are required before legal review",
                )

        if current == "under_objection" and target == "legal_review" and open_objections:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resolve or dismiss all open objections before returning to legal review.",
            )

    def _validate_pre_check_completeness(self, application: dict) -> None:
        """Applicant and parcel data must be fully on file before pre-check can complete."""
        applicant = application.get("applicant") or {}
        missing_applicant = [f for f in REQUIRED_APPLICANT_FIELDS if not str(applicant.get(f) or "").strip()]
        if missing_applicant:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Cannot transition to 'pre_checked': applicant information is incomplete "
                    f"(missing: {', '.join(missing_applicant)})."
                ),
            )

        parcel_ref = application.get("parcel_ref") or {}
        missing_parcel_fields = [f for f in REQUIRED_PARCEL_REF_FIELDS if not str(parcel_ref.get(f) or "").strip()]
        if missing_parcel_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Cannot transition to 'pre_checked': parcel information is incomplete "
                    f"(missing: {', '.join(missing_parcel_fields)})."
                ),
            )

        parcel_code = parcel_ref.get("parcel_code")
        if not parcel_code or not self._parcel_repo.get_by_code(parcel_code):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Cannot transition to 'pre_checked': no parcel record found for "
                    f"parcel_code '{parcel_code or ''}'."
                ),
            )

    def _validate_survey_report_exists(self, application: dict) -> None:
        """A field survey report must be on file before the survey stage can complete."""
        survey = application.get("survey") or {}
        if not survey.get("report"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot transition to 'surveyed': no survey report has been submitted for this application.",
            )

    def build_update(self, application: dict, target: str, reason: str | None) -> dict:
        """Return the MongoDB $set payload for the status transition."""
        current = application["status"]
        now = datetime.now(timezone.utc)

        update: dict = {
            "status": target,
            "timestamps.updated_at": now,
        }

        # Track where to resume once a pause state is resolved.
        if target in RESUMABLE_STATUSES:
            update["previous_status"] = current
        elif current in RESUMABLE_STATUSES:
            update["previous_status"] = None

        update["hold_reason"] = reason if target == "on_hold" else (None if current == "on_hold" else application.get("hold_reason"))
        update["missing_documents_reason"] = (
            reason if target == "missing_documents" else (None if current == "missing_documents" else application.get("missing_documents_reason"))
        )
        update["objection_reason"] = (
            reason if target == "under_objection" else (None if current == "under_objection" else application.get("objection_reason"))
        )

        if target == "rejected":
            update["rejection_reason"] = reason

        if target == "survey_required":
            update["survey.status"] = "scheduled"
        if target == "surveyed":
            update["survey.status"] = "completed"

        if target == "closed":
            update["timestamps.completed_at"] = now

        return update
