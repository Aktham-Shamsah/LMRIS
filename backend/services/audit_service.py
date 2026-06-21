from models.audit_log import AuditLogModel, AUDIT_ACTIONS
from database.connection import db


class AuditService:
    """Write performance/audit logs for every important action."""

    def __init__(self) -> None:
        self._col = db[AuditLogModel.collection_name]

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        performed_by: str = "system",
        details: dict | None = None,
    ) -> None:
        if action not in AUDIT_ACTIONS:
            raise ValueError(f"Unknown audit action: {action}")
        doc = AuditLogModel.new(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=performed_by,
            details=details,
        )
        self._col.insert_one(doc)

    # Convenience methods ------------------------------------------------

    def application_created(self, application_id: str, application_type: str, by: str = "system") -> None:
        self.log("application_created", "application", application_id, by,
                 {"application_type": application_type})

    def status_changed(self, application_id: str, old: str, new: str, by: str = "system") -> None:
        self.log("status_changed", "application", application_id, by,
                 {"from": old, "to": new})

    def hold_placed(self, application_id: str, reason: str, by: str = "system") -> None:
        self.log("hold_placed", "application", application_id, by, {"reason": reason})

    def rejection_issued(self, application_id: str, reason: str, by: str = "system") -> None:
        self.log("rejection_issued", "application", application_id, by, {"reason": reason})

    def missing_documents_flagged(self, application_id: str, reason: str, by: str = "system") -> None:
        self.log("missing_documents_flagged", "application", application_id, by, {"reason": reason})

    def objection_raised(self, application_id: str, reason: str, by: str = "system") -> None:
        self.log("objection_raised", "application", application_id, by, {"reason": reason})

    def certificate_generated(self, certificate_id: str, application_id: str, by: str = "system") -> None:
        self.log("certificate_generated", "certificate", certificate_id, by,
                 {"application_id": application_id})

    def attachment_uploaded(self, application_id: str, doc_id: str, filename: str, by: str = "system") -> None:
        self.log("attachment_uploaded", "application", application_id, by,
                 {"doc_id": doc_id, "filename": filename})

    def attachment_verified(self, application_id: str, doc_id: str, by: str = "system") -> None:
        self.log("attachment_verified", "application", application_id, by, {"doc_id": doc_id})

    def attachment_deleted(self, application_id: str, doc_id: str, filename: str, by: str = "system") -> None:
        self.log("attachment_deleted", "application", application_id, by,
                 {"doc_id": doc_id, "filename": filename})

    def note_added(self, application_id: str, note_id: str, by: str = "system") -> None:
        self.log("note_added", "application", application_id, by, {"note_id": note_id})

    def survey_report_submitted(self, application_id: str, by: str = "system") -> None:
        self.log("survey_report_submitted", "application", application_id, by, {})
