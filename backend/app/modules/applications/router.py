from fastapi import APIRouter, Header, Query

from app.modules.applications.models import (
    ApplicationCreate,
    CommentCreate,
    DocumentCreate,
    ObjectionCreate,
    ReasonRequest,
    TransitionRequest,
)
from app.modules.applications.service import ApplicationService
from app.shared.pagination import paginated
from app.shared.responses import ok

router = APIRouter(prefix="/applications", tags=["Applications"])
service = ApplicationService()


@router.post("/", status_code=201)
def create_application(payload: ApplicationCreate, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    return ok(service.create(payload, idempotency_key), "Application created.")


@router.get("/")
def list_applications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    application_type: str | None = None,
    zone_id: str | None = None,
    dispute_state: str | None = None,
    search: str | None = None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
):
    items, total = service.list(
        page=page,
        limit=limit,
        status=status,
        application_type=application_type,
        zone_id=zone_id,
        dispute_state=dispute_state,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ok(paginated(items, total, page, limit))


@router.get("/{application_id}")
def get_application(application_id: str):
    return ok(service.get(application_id))


@router.patch("/{application_id}/transition")
def transition_application(application_id: str, payload: TransitionRequest):
    return ok(service.transition(application_id, payload), "Application status updated.")


@router.post("/{application_id}/hold")
def hold_application(application_id: str, payload: ReasonRequest):
    return ok(service.hold(application_id, payload), "Application placed on hold.")


@router.post("/{application_id}/reject")
def reject_application(application_id: str, payload: ReasonRequest):
    return ok(service.reject(application_id, payload), "Application rejected.")


@router.post("/{application_id}/certificate", status_code=201)
def issue_certificate(application_id: str, performed_by: str = "registrar"):
    return ok(service.issue_certificate(application_id, performed_by), "Certificate issued.")


@router.post("/{application_id}/documents", status_code=201)
def add_document(application_id: str, payload: DocumentCreate):
    return ok(service.add_document(application_id, payload), "Document metadata added.")


@router.post("/{application_id}/comments", status_code=201)
def add_comment(application_id: str, payload: CommentCreate):
    return ok(service.add_comment(application_id, payload), "Comment added.")


@router.post("/{application_id}/objections", status_code=201)
def add_objection(application_id: str, payload: ObjectionCreate):
    return ok(service.add_objection(application_id, payload), "Objection submitted.")


@router.get("/{application_id}/timeline")
def get_timeline(application_id: str):
    return ok({"items": service.timeline(application_id)})

