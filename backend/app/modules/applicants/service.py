from fastapi import HTTPException, status

from app.modules.applicants.models import ApplicantCreate
from app.modules.applicants.repository import ApplicantRepository
from app.shared.ids import utc_now


class ApplicantService:
    def __init__(self, repo: ApplicantRepository | None = None) -> None:
        self.repo = repo or ApplicantRepository()

    def create(self, payload: ApplicantCreate) -> dict:
        existing = self.repo.get_by_national_id(payload.identity.national_id)
        if existing:
            return existing
        now = utc_now()
        doc = payload.model_dump(mode="json")
        doc.update(
            {
                "applicant_id": f"APP-{payload.identity.national_id}",
                "linked_applications": [],
                "stats": {"total_applications": 0, "approved_applications": 0, "pending_applications": 0},
                "created_at": now,
                "updated_at": now,
            }
        )
        return self.repo.create(doc)

    def get(self, applicant_id: str) -> dict:
        doc = self.repo.get(applicant_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found.")
        restricted = dict(doc)
        restricted.pop("_id", None)
        return restricted

    def applications(self, applicant_id: str) -> list[dict]:
        if not self.repo.get(applicant_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found.")
        return self.repo.applications(applicant_id)

