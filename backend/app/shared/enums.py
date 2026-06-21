from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ApplicationStatus(StrEnum):
    SUBMITTED = "submitted"
    PRE_CHECKED = "pre_checked"
    SURVEY_REQUIRED = "survey_required"
    SURVEYED = "surveyed"
    LEGAL_REVIEW = "legal_review"
    APPROVED = "approved"
    CERTIFICATE_ISSUED = "certificate_issued"
    CLOSED = "closed"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"
    MISSING_DOCUMENTS = "missing_documents"
    UNDER_OBJECTION = "under_objection"


class ApplicationType(StrEnum):
    FIRST_REGISTRATION = "first_registration"
    OWNERSHIP_TRANSFER = "ownership_transfer"
    PARCEL_SUBDIVISION = "parcel_subdivision"
    PARCEL_MERGE = "parcel_merge"
    BOUNDARY_CORRECTION = "boundary_correction"
    CERTIFICATE_REQUEST = "certificate_request"


class ApplicantType(StrEnum):
    CITIZEN = "citizen"
    LAWYER = "lawyer"
    COMPANY = "company"
    SURVEYOR = "surveyor"
    AUTHORIZED_REPRESENTATIVE = "authorized_representative"


class VerificationState(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    SUSPENDED = "suspended"


class DocumentStatus(StrEnum):
    MISSING = "missing"
    UPLOADED = "uploaded"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class SurveyMilestone(StrEnum):
    ASSIGNED = "assigned"
    VISIT_SCHEDULED = "visit_scheduled"
    ARRIVED_ON_SITE = "arrived_on_site"
    SURVEY_STARTED = "survey_started"
    SURVEY_COMPLETED = "survey_completed"
    REPORT_UPLOADED = "report_uploaded"
    REGISTRAR_REVIEWED = "registrar_reviewed"


class StaffRole(StrEnum):
    SURVEYOR = "surveyor"
    REGISTRAR = "registrar"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

