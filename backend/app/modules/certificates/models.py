from pydantic import BaseModel


class CertificateResponse(BaseModel):
    certificate_id: str
    application_id: str
    status: str
    issued_at: str | None = None

