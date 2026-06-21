from fastapi import APIRouter, Depends

from app.core.security import require_supervisor_role
from app.modules.staff.models import StaffCreate
from app.modules.staff.service import StaffService
from app.shared.responses import ok

router = APIRouter(prefix="/staff", tags=["Staff"], dependencies=[Depends(require_supervisor_role)])
service = StaffService()


@router.post("/", status_code=201)
def create_staff(payload: StaffCreate):
    return ok(service.create(payload), "Staff member created.")


@router.get("/{staff_id}")
def get_staff(staff_id: str):
    return ok(service.get(staff_id))

