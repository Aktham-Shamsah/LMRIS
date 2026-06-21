from fastapi import HTTPException, status

from app.modules.staff.models import StaffCreate
from app.modules.staff.repository import StaffRepository
from app.shared.ids import utc_now


class StaffService:
    def __init__(self, repo: StaffRepository | None = None) -> None:
        self.repo = repo or StaffRepository()

    def create(self, payload: StaffCreate) -> dict:
        role_prefix = {"surveyor": "SURV", "registrar": "REG", "staff": "STF", "manager": "MGR"}[payload.role.value]
        zone = payload.coverage.zone_ids[0].replace("ZONE-", "").replace("-0", "-") if payload.coverage.zone_ids else "GEN"
        count = self.repo.count_by_role(payload.role.value) + 1
        staff_code = payload.staff_code or f"{role_prefix}-{zone}-{count:02d}"
        now = utc_now()
        doc = payload.model_dump(mode="json")
        doc.update({"staff_id": staff_code, "staff_code": staff_code, "created_at": now, "updated_at": now})
        return self.repo.create(doc)

    def get(self, staff_id: str) -> dict:
        doc = self.repo.get(staff_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")
        doc["performance_summary"] = self.repo.workload_summary(doc["staff_code"])
        return doc

