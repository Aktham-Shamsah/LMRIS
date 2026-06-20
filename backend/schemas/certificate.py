from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class CertificateCreate(BaseModel):
    application_id: str = Field(..., description="Reference to the approved land application")
    parcel_code: str = Field(..., min_length=1, max_length=50)
    owner_name: str = Field(..., min_length=1, max_length=200)
    certificate_type: str = Field(..., min_length=1, max_length=100)
    valid_until: Optional[datetime] = None
    performed_by: str = Field(default="system", max_length=100)


class CertificateIssueRequest(BaseModel):
    valid_until: Optional[datetime] = Field(
        default=None, description="Optional expiry date; omit for a certificate valid indefinitely.",
    )
    certificate_type: Optional[str] = Field(
        default=None, max_length=100,
        description="Defaults to the application's type (e.g. 'ownership_transfer') if not provided.",
    )
    performed_by: str = Field(default="system", max_length=100)


class CertificateResponse(BaseModel):
    id: str
    certificate_id: str
    application_id: str
    parcel_code: str
    owner_name: str
    certificate_type: str
    issued_at: datetime
    valid_until: Optional[datetime]
    status: str


class CertificateListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[CertificateResponse]
