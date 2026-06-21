from app.modules.applicants.models import ApplicantCreate
from app.modules.applicants.service import ApplicantService
from app.modules.applications.models import ApplicationCreate, ApplicantRef, DocumentCreate, ParcelRef
from app.shared.enums import ApplicantType, ApplicationType


def make_applicant_payload(national_id="400000000"):
    return ApplicantCreate(
        full_name="Nour Ahmad",
        applicant_type=ApplicantType.CITIZEN,
        identity={"national_id": national_id, "verified": True},
        contacts={"email": "nour@example.com", "phone": "+970599000000"},
        address={"city": "Ramallah", "zone_id": "ZONE-RM-01"},
    )


def make_application_payload():
    return ApplicationCreate(
        application_type=ApplicationType.OWNERSHIP_TRANSFER,
        applicant_ref=ApplicantRef(applicant_id="APP-400000000", applicant_type=ApplicantType.CITIZEN),
        parcel_ref=ParcelRef(parcel_number="145", block_number="12", basin_number="3", zone_id="ZONE-RM-01"),
        description="Ownership transfer test",
        idempotency_key="idem-1",
    )


def test_applicant_creation(db):
    service = ApplicantService()
    service.repo.db = db
    service.repo.collection = db.applicants
    applicant = service.create(make_applicant_payload())
    assert applicant["applicant_id"] == "APP-400000000"
    assert applicant["verification_state"] == "unverified"


def test_document_upload_metadata(application_service):
    app = application_service.create(make_application_payload())
    document = application_service.add_document(
        app["application_id"],
        DocumentCreate(
            document_type="ownership_deed",
            filename="deed.pdf",
            status="uploaded",
            is_ownership_doc=True,
        ),
    )
    assert document["application_id"] == app["application_id"]
    assert document["document_type"] == "ownership_deed"

