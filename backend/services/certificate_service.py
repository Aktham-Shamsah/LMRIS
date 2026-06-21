from __future__ import annotations
from typing import Optional
from fastapi import HTTPException, status
from repositories.certificate_repository import CertificateRepository
from repositories.application_repository import ApplicationRepository
from models.certificate import CertificateModel
from schemas.certificate import CertificateCreate
from services.audit_service import AuditService


class CertificateService:
    def __init__(self) -> None:
        self._repo = CertificateRepository()
        self._app_repo = ApplicationRepository()
        self._audit = AuditService()

    def generate(self, payload: CertificateCreate) -> dict:
        # Validate the linked application exists and is approved/completed
        app = self._app_repo.get_by_application_id(payload.application_id)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application '{payload.application_id}' not found.",
            )
        if app["status"] not in ("approved", "certificate_issued"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Certificates can only be issued for approved applications.",
            )
        doc = CertificateModel.new(
            application_id=payload.application_id,
            parcel_code=payload.parcel_code,
            owner_name=payload.owner_name,
            certificate_type=payload.certificate_type,
            valid_until=payload.valid_until,
        )
        created = self._repo.create(doc)
        self._audit.certificate_generated(created["certificate_id"], payload.application_id, payload.performed_by)
        return created

    def get(self, cert_id: str) -> dict:
        cert = self._repo.get_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")
        return cert

    def list(
        self,
        skip: int,
        limit: int,
        parcel_code: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        return self._repo.list(skip=skip, limit=limit, parcel_code=parcel_code)

    def revoke(self, cert_id: str) -> dict:
        self.get(cert_id)
        revoked = self._repo.revoke(cert_id)
        if not revoked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")
        return revoked
