from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    log_id: str
    action: str
    entity_type: str
    entity_id: str
    performed_by: str
    details: dict
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[AuditLogResponse]
