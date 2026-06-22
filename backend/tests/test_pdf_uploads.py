from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from starlette.datastructures import Headers

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


def test_application_document_upload_requires_and_stores_pdf(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.shared.files.get_settings", lambda: UploadSettings(tmp_path))
    now = utc_now()
    db.land_applications.insert_one(
        {
            "application_id": "LRMIS-2026-9100",
            "application_type": "ownership_transfer",
            "status": "submitted",
            "priority": "normal",
            "applicant_ref": {"applicant_id": "APP-555000111", "applicant_type": "citizen"},
            "parcel_ref": {"parcel_code": "RM-Z01-B12-P145", "parcel_number": "145", "block_number": "12", "basin_number": "3", "zone_id": "ZONE-RM-01"},
            "workflow": {"current_state": "submitted", "allowed_next": ["pre_checked"]},
            "required_documents": [{"document_type": "ownership_deed", "required": True, "status": "missing"}],
            "documents": [],
            "timestamps": {"submitted_at": now, "updated_at": now},
            "legal_review": {"completed": False},
            "objection": {"has_objection": False, "objection_ids": []},
        }
    )
    service = ApplicationService(
        ApplicationRepository(db),
        ApplicantRepository(db),
        AuditService(AuditRepository(db)),
        NotificationService(db),
    )
    upload = UploadFile(
        file=BytesIO(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"),
        filename="ownership.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )

    document = service.upload_document(
        "LRMIS-2026-9100",
        document_type="ownership_deed",
        file=upload,
        uploaded_by="APP-555000111",
        is_ownership_doc=True,
    )

    assert document["content_type"] == "application/pdf"
    assert (tmp_path / document["storage_path"]).exists()
    app = db.land_applications.find_one({"application_id": "LRMIS-2026-9100"})
    assert app["required_documents"][0]["status"] == "uploaded"
