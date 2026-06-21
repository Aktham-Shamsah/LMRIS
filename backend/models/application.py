from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import uuid


class ApplicationModel:
    collection_name = "land_applications"

    APPLICATION_TYPES = [
        "first_registration",
        "ownership_transfer",
        "parcel_subdivision",
        "parcel_merge",
        "boundary_correction",
        "certificate_request",
    ]

    # Main workflow pipeline, in order.
    MAIN_FLOW_STATUSES = [
        "submitted",
        "pre_checked",
        "survey_required",
        "surveyed",
        "legal_review",
        "approved",
        "certificate_issued",
        "closed",
    ]

    # Side states an application can be diverted into from the main flow.
    ALTERNATIVE_STATUSES = ["rejected", "on_hold", "missing_documents", "under_objection"]

    STATUSES = MAIN_FLOW_STATUSES + ALTERNATIVE_STATUSES

    # Application types where a field survey must happen before approval.
    SURVEY_REQUIRED_TYPES = {
        "first_registration",
        "parcel_subdivision",
        "parcel_merge",
        "boundary_correction",
    }

    @staticmethod
    def generate_id() -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short = uuid.uuid4().hex[:6].upper()
        return f"APP-{date_str}-{short}"

    @staticmethod
    def new(
        application_type: str,
        applicant: dict,
        parcel_ref: dict,
        notes: str = "",
        idempotency_key: Optional[str] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        doc: dict = {
            "application_id": ApplicationModel.generate_id(),
            "application_type": application_type,
            "status": "submitted",
            "applicant": applicant,
            "parcel_ref": parcel_ref,
            "documents": [],
            "survey": {
                "status": "pending" if application_type in ApplicationModel.SURVEY_REQUIRED_TYPES else "not_required",
                "report": None,
            },
            "objections": [],
            "notes": notes,
            "internal_notes": [],
            "previous_status": None,
            "hold_reason": None,
            "hold_history": [],
            "rejection_reason": None,
            "rejection_history": [],
            "missing_documents_reason": None,
            "objection_reason": None,
            "timestamps": {
                "created_at": now,
                "submitted_at": now,
                "updated_at": now,
                "completed_at": None,
            },
        }
        if idempotency_key:
            doc["idempotency_key"] = idempotency_key
        return doc

    @staticmethod
    def serialize(doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
