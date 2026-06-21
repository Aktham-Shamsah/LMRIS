from typing import Optional
from fastapi import APIRouter, Query
from schemas.certificate import CertificateCreate, CertificateResponse, CertificateListResponse
from schemas.common import APIResponse, PaginationParams
from services.certificate_service import CertificateService

router = APIRouter(prefix="/certificates", tags=["Certificates"])
_svc = CertificateService()


@router.post(
    "",
    response_model=APIResponse[CertificateResponse],
    status_code=201,
    summary="Generate a land certificate for an approved application",
)
def generate_certificate(payload: CertificateCreate):
    return APIResponse(data=_svc.generate(payload), message="Certificate generated.")


@router.get(
    "",
    response_model=APIResponse[CertificateListResponse],
    summary="List certificates with optional parcel filter",
)
def list_certificates(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    parcel_code: Optional[str] = Query(default=None),
):
    params = PaginationParams(page=page, limit=limit)
    items, total = _svc.list(skip=params.skip, limit=params.limit, parcel_code=parcel_code)
    return APIResponse(data=CertificateListResponse(total=total, page=page, limit=limit, items=items))


@router.get(
    "/{cert_id}",
    response_model=APIResponse[CertificateResponse],
    summary="Get certificate by ID",
)
def get_certificate(cert_id: str):
    return APIResponse(data=_svc.get(cert_id))


@router.patch(
    "/{cert_id}/revoke",
    response_model=APIResponse[CertificateResponse],
    summary="Revoke a certificate",
)
def revoke_certificate(cert_id: str):
    return APIResponse(data=_svc.revoke(cert_id), message="Certificate revoked.")
