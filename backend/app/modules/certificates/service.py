from fastapi import HTTPException, status

from app.modules.certificates.repository import CertificateRepository


class CertificateService:
    def __init__(self, repo: CertificateRepository | None = None) -> None:
        self.repo = repo or CertificateRepository()

    def get(self, certificate_id: str) -> dict:
        doc = self.repo.get(certificate_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")
        return doc

    def by_application(self, application_id: str) -> dict:
        doc = self.repo.by_application(application_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found for application.")
        return doc

