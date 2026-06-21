from fastapi import APIRouter

from app.modules.applicants.models import ApplicantCreate
from app.modules.applicants.service import ApplicantService
from app.shared.responses import ok

router = APIRouter(prefix="/applicants", tags=["Applicants"])
service = ApplicantService()


@router.post("/", status_code=201)
def create_applicant(payload: ApplicantCreate):
    return ok(service.create(payload), "Applicant profile created.")


@router.get("/{applicant_id}")
def get_applicant(applicant_id: str):
    return ok(service.get(applicant_id))


@router.get("/{applicant_id}/applications")
def get_applicant_applications(applicant_id: str):
    return ok({"items": service.applications(applicant_id)})

