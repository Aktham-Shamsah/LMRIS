from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field
from schemas.parcel import ParcelResponse


ApplicationType = Literal[
    "first_registration",
    "ownership_transfer",
    "parcel_subdivision",
    "parcel_merge",
    "boundary_correction",
    "certificate_request",
]

ApplicationStatus = Literal[
    "submitted",
    "pre_checked",
    "survey_required",
    "surveyed",
    "legal_review",
    "approved",
    "certificate_issued",
    "closed",
    "rejected",
    "on_hold",
    "missing_documents",
    "under_objection",
]

SurveyStatus = Literal["not_required", "pending", "scheduled", "completed"]
ObjectionStatus = Literal["open", "resolved", "dismissed"]
CertificateStatusValue = Literal["not_issued", "active", "revoked"]


class ApplicantSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(default="", max_length=30)
    national_id: str = Field(..., min_length=1, max_length=50)


class ParcelRefSchema(BaseModel):
    parcel_number: str = Field(..., min_length=1, max_length=50)
    block_number: str = Field(..., min_length=1, max_length=50)
    basin_number: str = Field(..., min_length=1, max_length=50)
    zone_id: str = Field(..., min_length=1, max_length=50)
    parcel_code: str = Field(default="", max_length=50)


class DocumentSchema(BaseModel):
    doc_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    uploaded_by: str
    verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None


class ApplicationTimestamps(BaseModel):
    created_at: datetime
    submitted_at: Optional[datetime] = None
    updated_at: datetime
    completed_at: Optional[datetime] = None


class ApplicationCreate(BaseModel):
    application_type: ApplicationType
    applicant: ApplicantSchema
    parcel_ref: ParcelRefSchema
    notes: str = Field(default="", max_length=2000)
    idempotency_key: Optional[str] = Field(default=None, max_length=100)


class ApplicationUpdate(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=2000)
    applicant: Optional[ApplicantSchema] = None
    parcel_ref: Optional[ParcelRefSchema] = None


class StatusTransitionRequest(BaseModel):
    new_status: ApplicationStatus
    reason: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Required for on_hold, rejected, missing_documents, and under_objection transitions.",
    )
    performed_by: str = Field(default="system", max_length=100)


class HoldRequest(BaseModel):
    reason: str = Field(
        ..., min_length=1, max_length=1000,
        description="Mandatory reason for placing the application on hold.",
    )
    performed_by: str = Field(default="system", max_length=100)


class HoldHistoryEntry(BaseModel):
    reason: str
    held_by: str
    held_at: datetime


class RejectRequest(BaseModel):
    reason: str = Field(
        ..., min_length=1, max_length=1000,
        description="Mandatory reason for rejecting the application.",
    )
    performed_by: str = Field(default="system", max_length=100)


class RejectionHistoryEntry(BaseModel):
    reason: str
    rejected_by: str
    rejected_at: datetime


class AttachmentVerify(BaseModel):
    performed_by: str = Field(default="system", max_length=100)


class AttachmentListResponse(BaseModel):
    total: int
    items: list[DocumentSchema]


class NoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Internal note / registrar remark text.")
    performed_by: str = Field(default="system", max_length=100)


class NoteEntry(BaseModel):
    note_id: str
    text: str
    created_by: str
    created_at: datetime


class NoteListResponse(BaseModel):
    total: int
    items: list[NoteEntry]


class ApplicationResponse(BaseModel):
    id: str
    application_id: str
    application_type: str
    status: str
    applicant: ApplicantSchema
    parcel_ref: ParcelRefSchema
    documents: list[DocumentSchema]
    notes: str
    internal_notes: list[NoteEntry] = []
    previous_status: Optional[str] = None
    hold_reason: Optional[str]
    hold_history: list[HoldHistoryEntry] = []
    rejection_reason: Optional[str]
    rejection_history: list[RejectionHistoryEntry] = []
    missing_documents_reason: Optional[str] = None
    objection_reason: Optional[str] = None
    timestamps: ApplicationTimestamps


class ApplicationListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[ApplicationResponse]


class SurveyReportCreate(BaseModel):
    surveyor_name: str = Field(..., min_length=1, max_length=200)
    survey_date: datetime
    findings: str = Field(..., min_length=1, max_length=2000)
    performed_by: str = Field(default="system", max_length=100)


class SurveyReportSchema(BaseModel):
    surveyor_name: str
    survey_date: datetime
    findings: str
    submitted_by: str
    submitted_at: datetime


class SurveySchema(BaseModel):
    status: SurveyStatus
    report: Optional[SurveyReportSchema] = None


class ObjectionSchema(BaseModel):
    objection_id: str
    objector_name: str
    reason: str
    status: ObjectionStatus
    filed_at: datetime


class WorkflowHistoryEntry(BaseModel):
    from_status: Optional[str]
    to_status: str
    performed_by: str
    timestamp: datetime


class WorkflowStateSchema(BaseModel):
    current_status: ApplicationStatus
    allowed_next_statuses: list[str]
    previous_status: Optional[str]
    hold_reason: Optional[str]
    hold_history: list[HoldHistoryEntry]
    rejection_reason: Optional[str]
    rejection_history: list[RejectionHistoryEntry]
    missing_documents_reason: Optional[str]
    objection_reason: Optional[str]
    history: list[WorkflowHistoryEntry]


class CertificateStatusSchema(BaseModel):
    status: CertificateStatusValue
    certificate_id: Optional[str] = None
    issued_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class ApplicationDetailResponse(BaseModel):
    application: ApplicationResponse
    workflow: WorkflowStateSchema
    parcel: Optional[ParcelResponse]
    attachments: list[DocumentSchema]
    survey: SurveySchema
    objections: list[ObjectionSchema]
    certificate: CertificateStatusSchema
    internal_notes: list[NoteEntry]
