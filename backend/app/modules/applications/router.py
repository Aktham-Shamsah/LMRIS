from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.security import get_current_user, require_roles
from app.modules.auth.models import CurrentUser
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
def create_application(
    payload: ApplicationCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(require_roles("applicant", "supervisor", "admin")),
):
    if user.role == "applicant" and payload.applicant_ref.applicant_id != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only submit their own applications.")
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
    user: CurrentUser = Depends(require_roles("registrar", "supervisor", "admin")),
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
def get_application(application_id: str, user: CurrentUser = Depends(get_current_user)):
    app = service.get(application_id)
    if user.role == "applicant" and app.get("applicant_ref", {}).get("applicant_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only view their own applications.")
    return ok(app)


@router.patch("/{application_id}/transition")
def transition_application(
    application_id: str,
    payload: TransitionRequest,
    user: CurrentUser = Depends(require_roles("registrar", "supervisor", "admin")),
):
    if payload.performed_by == "staff":
        payload.performed_by = user.actor_id or user.email
    return ok(service.transition(application_id, payload), "Application status updated.")


@router.post("/{application_id}/hold")
def hold_application(
    application_id: str,
    payload: ReasonRequest,
    user: CurrentUser = Depends(require_roles("registrar", "supervisor", "admin")),
):
    if payload.performed_by == "staff":
        payload.performed_by = user.actor_id or user.email
    return ok(service.hold(application_id, payload), "Application placed on hold.")


@router.post("/{application_id}/reject")
def reject_application(
    application_id: str,
    payload: ReasonRequest,
    user: CurrentUser = Depends(require_roles("registrar", "supervisor", "admin")),
):
    if payload.performed_by == "staff":
        payload.performed_by = user.actor_id or user.email
    return ok(service.reject(application_id, payload), "Application rejected.")


@router.post("/{application_id}/certificate", status_code=201)
def issue_certificate(
    application_id: str,
    performed_by: str = "registrar",
    user: CurrentUser = Depends(require_roles("registrar", "supervisor", "admin")),
):
    return ok(service.issue_certificate(application_id, user.actor_id or performed_by), "Certificate issued.")


@router.post("/{application_id}/documents", status_code=201)
def add_document(application_id: str, payload: DocumentCreate, user: CurrentUser = Depends(get_current_user)):
    app = service.get(application_id)
    if user.role == "applicant" and app.get("applicant_ref", {}).get("applicant_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only update their own applications.")
    if payload.uploaded_by == "applicant":
        payload.uploaded_by = user.actor_id or user.email
    return ok(service.add_document(application_id, payload), "Document metadata added.")


@router.post("/{application_id}/comments", status_code=201)
def add_comment(application_id: str, payload: CommentCreate, user: CurrentUser = Depends(get_current_user)):
    app = service.get(application_id)
    if user.role == "applicant" and app.get("applicant_ref", {}).get("applicant_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only comment on their own applications.")
    return ok(service.add_comment(application_id, payload), "Comment added.")


@router.post("/{application_id}/objections", status_code=201)
def add_objection(application_id: str, payload: ObjectionCreate, user: CurrentUser = Depends(require_roles("applicant", "supervisor", "admin"))):
    app = service.get(application_id)
    if user.role == "applicant" and app.get("applicant_ref", {}).get("applicant_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only object on their own applications.")
    if user.role == "applicant":
        payload.submitted_by = user.actor_id or payload.submitted_by
    return ok(service.add_objection(application_id, payload), "Objection submitted.")


@router.get("/{application_id}/timeline")
def get_timeline(application_id: str, user: CurrentUser = Depends(get_current_user)):
    app = service.get(application_id)
    if user.role == "applicant" and app.get("applicant_ref", {}).get("applicant_id") != user.actor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Applicants can only view their own timeline.")
    return ok({"items": service.timeline(application_id)})

