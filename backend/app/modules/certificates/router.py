from fastapi import APIRouter

from app.modules.certificates.service import CertificateService
from app.shared.responses import ok

router = APIRouter(prefix="/certificates", tags=["Certificates"])
service = CertificateService()


@router.get("/application/{application_id}/latest")
def get_application_certificate(application_id: str):
    return ok(service.by_application(application_id))


@router.get("/{certificate_id}")
def get_certificate(certificate_id: str):
    return ok(service.get(certificate_id))
