from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user, require_roles
from app.modules.auth.models import CurrentUser
from app.modules.applicants.models import ApplicantCreate
from app.modules.applicants.service import ApplicantService
from app.shared.responses import ok

router = APIRouter(prefix="/applicants", tags=["Applicants"])
service = ApplicantService()


@router.post("/", status_code=201)
def create_applicant(payload: ApplicantCreate, user: CurrentUser = Depends(require_roles("applicant", "supervisor", "admin"))):
    if user.role == "applicant" and user.actor_id and user.actor_id != f"APP-{payload.identity.national_id}":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only create their own profile.")
    return ok(service.create(payload), "Applicant profile created.")


@router.get("/{applicant_id}")
def get_applicant(applicant_id: str, user: CurrentUser = Depends(get_current_user)):
    if user.role == "applicant" and user.actor_id != applicant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only view their own profile.")
    return ok(service.get(applicant_id))


@router.get("/{applicant_id}/applications")
def get_applicant_applications(applicant_id: str, user: CurrentUser = Depends(get_current_user)):
    if user.role == "applicant" and user.actor_id != applicant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only view their own applications.")
    return ok({"items": service.applications(applicant_id)})

