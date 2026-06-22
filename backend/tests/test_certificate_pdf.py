from pathlib import Path

from app.modules.applicants.repository import ApplicantRepository
from app.modules.applications.repository import ApplicationRepository
from app.modules.applications.service import ApplicationService
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.notifications.service import NotificationService
from app.shared.ids import utc_now


class UploadSettings:
    def __init__(self, upload_dir: Path):
        self.upload_dir = str(upload_dir)
        self.max_upload_size_mb = 10


def test_issue_certificate_generates_stored_pdf(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.shared.files.get_settings", lambda: UploadSettings(tmp_path))
    now = utc_now()
    db.applicants.insert_one(
        {
            "applicant_id": "APP-555000111",
            "full_name": "New Applicant",
            "contacts": {"email": "new@example.com"},
            "preferences": {"notifications": {"on_certificate_ready": True}},
        }
    )
    db.land_applications.insert_one(
        {
            "application_id": "LRMIS-2026-9000",
            "application_type": "ownership_transfer",
            "status": "approved",
            "priority": "normal",
            "applicant_ref": {"applicant_id": "APP-555000111", "applicant_type": "citizen"},
            "parcel_ref": {
                "parcel_id": "RM-Z01-B12-P145",
                "parcel_code": "RM-Z01-B12-P145",
                "parcel_number": "145",
                "block_number": "12",
                "basin_number": "3",
                "zone_id": "ZONE-RM-01",
            },
            "workflow": {"current_state": "approved", "allowed_next": ["certificate_issued"]},
            "required_documents": [],
            "documents": [],
            "timestamps": {"approved_at": now, "updated_at": now},
            "legal_review": {"completed": True},
            "objection": {"has_objection": False, "objection_ids": []},
        }
    )
    service = ApplicationService(
        ApplicationRepository(db),
        ApplicantRepository(db),
        AuditService(AuditRepository(db)),
        NotificationService(db),
    )

    certificate = service.issue_certificate("LRMIS-2026-9000", "REG-RM-01")

    pdf_path = tmp_path / certificate["pdf"]["storage_path"]
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert db.land_applications.find_one({"application_id": "LRMIS-2026-9000"})["status"] == "certificate_issued"
