from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.modules.certificates.service import CertificateService
from app.shared.responses import ok

router = APIRouter(prefix="/certificates", tags=["Certificates"])
service = CertificateService()


@router.get("/application/{application_id}/latest")
def get_application_certificate(application_id: str, _user=Depends(get_current_user)):
    return ok(service.by_application(application_id))


@router.get("/{certificate_id}")
def get_certificate(certificate_id: str, _user=Depends(get_current_user)):
    return ok(service.get(certificate_id))
