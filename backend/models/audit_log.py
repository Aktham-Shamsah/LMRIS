from __future__ import annotations
from datetime import datetime, timezone
import uuid


AUDIT_ACTIONS = [
    "application_created",
    "status_changed",
    "hold_placed",
    "rejection_issued",
    "missing_documents_flagged",
    "objection_raised",
    "certificate_generated",
    "attachment_uploaded",
    "attachment_verified",
    "attachment_deleted",
    "note_added",
    "survey_report_submitted",
]


class AuditLogModel:
    collection_name = "performance_logs"

    @staticmethod
    def new(
        action: str,
        entity_type: str,
        entity_id: str,
        performed_by: str = "system",
        details: dict | None = None,
    ) -> dict:
        return {
            "log_id": uuid.uuid4().hex,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "performed_by": performed_by,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc),
        }

    @staticmethod
    def serialize(doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
