from typing import Literal, Optional
from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, ApplicationDetailResponse,
    ApplicationListResponse, StatusTransitionRequest, HoldRequest, RejectRequest,
    AttachmentVerify, AttachmentListResponse, DocumentSchema,
    NoteCreate, NoteEntry, NoteListResponse,
    SurveyReportCreate, SurveyReportSchema,
)
from schemas.certificate import CertificateIssueRequest, CertificateResponse
from schemas.common import APIResponse, PaginationParams
from services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Land Applications"])
_svc = ApplicationService()


@router.post(
    "",
    response_model=APIResponse[ApplicationResponse],
    status_code=201,
    summary="Submit a new land application",
)
def create_application(payload: ApplicationCreate):
    return APIResponse(data=_svc.create(payload), message="Application created.")


@router.get(
    "",
    response_model=APIResponse[ApplicationListResponse],
    summary="Search, filter, sort, and paginate applications",
)
def list_applications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    application_type: Optional[str] = Query(default=None, description="Filter by application type"),
    zone_id: Optional[str] = Query(default=None, description="Filter by zone ID"),
    search: Optional[str] = Query(
        default=None, max_length=200,
        description="Search by application ID, applicant name/email/national ID, or parcel code",
    ),
    sort_by: Literal[
        "created_at", "updated_at", "submitted_at", "completed_at", "status", "application_type"
    ] = Query(default="created_at", description="Field to sort by"),
    sort_order: Literal["asc", "desc"] = Query(default="desc", description="Sort direction"),
):
    params = PaginationParams(page=page, limit=limit)
    items, total = _svc.list(
        skip=params.skip, limit=params.limit,
        status_filter=status, type_filter=application_type, zone_id=zone_id,
        search=search, sort_by=sort_by, sort_order=sort_order,
    )
    return APIResponse(data=ApplicationListResponse(total=total, page=page, limit=limit, items=items))


@router.get(
    "/{app_id}",
    response_model=APIResponse[ApplicationDetailResponse],
    summary="Get full application details for review",
    description=(
        "Returns the application together with everything a registrar needs to review it: "
        "workflow state (current status, allowed next transitions, status history), "
        "parcel information, attachments, survey status, objections, and certificate status."
    ),
)
def get_application(app_id: str):
    return APIResponse(data=_svc.get_details(app_id))


@router.patch(
    "/{app_id}",
    response_model=APIResponse[ApplicationResponse],
    summary="Update a submitted (pending-review) application",
)
def update_application(app_id: str, payload: ApplicationUpdate):
    return APIResponse(data=_svc.update(app_id, payload), message="Application updated.")


@router.patch(
    "/{app_id}/transition",
    response_model=APIResponse[ApplicationResponse],
    summary="Transition application status (workflow state machine)",
    description=(
        "Applications are created with status **`submitted`**.\n\n"
        "Main workflow:\n"
        "`submitted` → `pre_checked` → `survey_required` → `surveyed` → `legal_review` "
        "→ `approved` → `certificate_issued` → `closed`\n\n"
        "Application types that don't require a field survey skip `survey_required`/`surveyed` "
        "and go straight from `pre_checked` to `legal_review`.\n\n"
        "Alternative states reachable from the main flow: `rejected` (terminal), `on_hold`, "
        "`missing_documents`, and `under_objection` (only from `legal_review`). `on_hold` and "
        "`missing_documents` resume back to the exact status they were entered from.\n\n"
        "`reason` is **required** for `on_hold`, `rejected`, `missing_documents`, and `under_objection`.\n\n"
        "All workflow rules (allowed transitions, required reasons, document verification, "
        "unresolved objections) are validated before the transition is applied."
    ),
)
def transition_status(app_id: str, req: StatusTransitionRequest):
    return APIResponse(data=_svc.transition(app_id, req), message="Status updated.")


@router.post(
    "/{app_id}/survey-report",
    response_model=APIResponse[SurveyReportSchema],
    status_code=201,
    summary="Submit a field survey report for an application",
    description=(
        "Records the field survey report (surveyor, survey date, findings) for an "
        "application. A survey report must be on file before the application can "
        "transition from `survey_required` to `surveyed`."
    ),
)
def submit_survey_report(app_id: str, payload: SurveyReportCreate):
    return APIResponse(data=_svc.submit_survey_report(app_id, payload), message="Survey report submitted.")


@router.post(
    "/{app_id}/hold",
    response_model=APIResponse[ApplicationResponse],
    summary="Place an application on hold (registrar action)",
    description=(
        "Pauses processing of an application until outstanding issues are resolved. "
        "A `reason` is **mandatory**. Every hold is appended to the application's "
        "`hold_history` in addition to being recorded in the audit log. "
        "The application resumes via `PATCH /applications/{app_id}/transition`, "
        "back to the exact status it was held from."
    ),
)
def hold_application(app_id: str, payload: HoldRequest):
    return APIResponse(data=_svc.place_on_hold(app_id, payload), message="Application placed on hold.")


@router.post(
    "/{app_id}/reject",
    response_model=APIResponse[ApplicationResponse],
    summary="Reject an application (registrar action)",
    description=(
        "Marks an application as rejected, ending the workflow. A `reason` is "
        "**mandatory**. Every rejection is appended to the application's "
        "`rejection_history` in addition to being recorded in the audit log."
    ),
)
def reject_application(app_id: str, payload: RejectRequest):
    return APIResponse(data=_svc.reject(app_id, payload), message="Application rejected.")


@router.post(
    "/{app_id}/certificate",
    response_model=APIResponse[CertificateResponse],
    status_code=201,
    summary="Generate a certificate for an approved application (registrar action)",
    description=(
        "Issues a certificate for an application in `approved` status, linking it to the "
        "application and recording its issuance date. Advances the application to "
        "`certificate_issued`. Parcel code and owner name are taken from the application; "
        "`certificate_type` defaults to the application's type unless overridden."
    ),
)
def issue_certificate(app_id: str, payload: CertificateIssueRequest):
    return APIResponse(data=_svc.issue_certificate(app_id, payload), message="Certificate generated.")


@router.post(
    "/{app_id}/attachments",
    response_model=APIResponse[DocumentSchema],
    status_code=201,
    summary="Upload a supporting document to an application",
    description=(
        "Accepts a multipart file upload (PDF, JPG, PNG, DOC, or DOCX, max 10MB) and stores it "
        "alongside metadata (filename, content type, size, uploader) for later ownership verification."
    ),
)
def upload_attachment(
    app_id: str,
    file: UploadFile = File(...),
    performed_by: str = Form(default="system"),
):
    return APIResponse(data=_svc.upload_attachment(app_id, file, performed_by), message="Attachment uploaded.")


@router.get(
    "/{app_id}/attachments",
    response_model=APIResponse[AttachmentListResponse],
    summary="List an application's attachments",
)
def list_attachments(app_id: str):
    items = _svc.list_attachments(app_id)
    return APIResponse(data=AttachmentListResponse(total=len(items), items=items))


@router.get(
    "/{app_id}/attachments/{attachment_id}/download",
    summary="Download or preview an attachment's file content",
)
def download_attachment(app_id: str, attachment_id: str):
    path, filename, content_type = _svc.get_attachment_file(app_id, attachment_id)
    return FileResponse(path, filename=filename, media_type=content_type)


@router.post(
    "/{app_id}/attachments/{attachment_id}/verify",
    response_model=APIResponse[DocumentSchema],
    summary="Mark an attachment as verified",
)
def verify_attachment(app_id: str, attachment_id: str, payload: AttachmentVerify):
    return APIResponse(
        data=_svc.verify_attachment(app_id, attachment_id, payload.performed_by),
        message="Attachment verified.",
    )


@router.delete(
    "/{app_id}/attachments/{attachment_id}",
    response_model=APIResponse[None],
    summary="Delete an attachment from an application",
)
def delete_attachment(app_id: str, attachment_id: str, performed_by: str = Query(default="system")):
    _svc.delete_attachment(app_id, attachment_id, performed_by)
    return APIResponse(message="Attachment deleted.")


@router.post(
    "/{app_id}/notes",
    response_model=APIResponse[NoteEntry],
    status_code=201,
    summary="Add an internal registrar note (registrar action)",
    description=(
        "Records an internal note or remark on an application, e.g. observations made "
        "during review that aren't part of a formal hold/rejection/objection reason. "
        "Internal notes are for registrar use only, are never shown to applicants, and "
        "form an append-only audit trail — each entry is timestamped, attributed to the "
        "registrar who wrote it, and also recorded in the audit log. Notes cannot be "
        "edited or deleted once added."
    ),
)
def add_note(app_id: str, payload: NoteCreate):
    return APIResponse(data=_svc.add_note(app_id, payload), message="Note added.")


@router.get(
    "/{app_id}/notes",
    response_model=APIResponse[NoteListResponse],
    summary="List an application's internal registrar notes",
)
def list_notes(app_id: str):
    items = _svc.list_notes(app_id)
    return APIResponse(data=NoteListResponse(total=len(items), items=items))


@router.delete(
    "/{app_id}",
    response_model=APIResponse[None],
    summary="Delete a draft application",
)
def delete_application(app_id: str):
    _svc.delete(app_id)
    return APIResponse(message="Application deleted.")
