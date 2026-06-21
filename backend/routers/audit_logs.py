from typing import Optional
from fastapi import APIRouter, Query
from schemas.audit_log import AuditLogResponse, AuditLogListResponse
from schemas.common import APIResponse, PaginationParams
from repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
_repo = AuditRepository()


@router.get(
    "",
    response_model=APIResponse[AuditLogListResponse],
    summary="List audit/performance logs with optional filters",
)
def list_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    entity_id: Optional[str] = Query(default=None, description="Filter by entity ID (application_id, cert_id, etc.)"),
    action: Optional[str] = Query(default=None, description="Filter by action type"),
):
    params = PaginationParams(page=page, limit=limit)
    items, total = _repo.list(skip=params.skip, limit=params.limit, entity_id=entity_id, action=action)
    return APIResponse(data=AuditLogListResponse(total=total, page=page, limit=limit, items=items))
