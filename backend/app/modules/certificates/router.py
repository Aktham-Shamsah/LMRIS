from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.security import get_current_user
from app.modules.auth.models import CurrentUser
from app.modules.certificates.service import CertificateService
from app.shared.files import stored_file_path
from app.shared.responses import ok

router = APIRouter(prefix="/certificates", tags=["Certificates"])
service = CertificateService()


@router.get("/application/{application_id}/latest")
def get_application_certificate(application_id: str, user: CurrentUser = Depends(get_current_user)):
    cert = service.by_application(application_id)
    _assert_can_view(cert, user)
    return ok(cert)


@router.get("/{certificate_id}/pdf")
def download_certificate_pdf(certificate_id: str, user: CurrentUser = Depends(get_current_user)):
    cert = service.get(certificate_id)
    _assert_can_view(cert, user)
    pdf = cert.get("pdf") or {}
    storage_path = pdf.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate PDF not found.")
    path = stored_file_path(storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate PDF file not found.")
    return FileResponse(path, media_type="application/pdf", filename=pdf.get("filename") or f"{certificate_id}.pdf")


@router.get("/{certificate_id}")
def get_certificate(certificate_id: str, user: CurrentUser = Depends(get_current_user)):
    cert = service.get(certificate_id)
    _assert_can_view(cert, user)
    return ok(cert)


def _assert_can_view(certificate: dict, user: CurrentUser) -> None:
    if user.role == "applicant" and certificate.get("issued_to", {}).get("applicant_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only view their own certificates.")
