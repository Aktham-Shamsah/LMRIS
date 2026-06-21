from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.shared.enums import ApplicantType, VerificationState


class Identity(BaseModel):
    national_id: str
    verified: bool = False
    verification_method: str | None = "otp_stub"


class Contacts(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None


class Address(BaseModel):
    city: str | None = None
    neighborhood: str | None = None
    zone_id: str | None = None
    line1: str | None = None


class NotificationPreferences(BaseModel):
    on_status_change: bool = True
    on_missing_documents: bool = True
    on_certificate_ready: bool = True


class Preferences(BaseModel):
    preferred_contact: str = "email"
    language: str = "ar"
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)


class PrivacySettings(BaseModel):
    share_contact_with_staff: bool = True
    public_certificate_lookup: bool = False


class ApplicantCreate(BaseModel):
    full_name: str
    applicant_type: ApplicantType
    identity: Identity
    contacts: Contacts = Field(default_factory=Contacts)
    address: Address = Field(default_factory=Address)
    verification_state: VerificationState = VerificationState.UNVERIFIED
    preferences: Preferences = Field(default_factory=Preferences)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)


class ApplicantResponse(ApplicantCreate):
    applicant_id: str
    linked_applications: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

