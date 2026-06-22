from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.shared.enums import ApplicantType


UserRole = Literal["applicant", "surveyor", "registrar", "supervisor", "admin"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    national_id: str = Field(min_length=4, max_length=40)
    phone: str | None = None
    applicant_type: ApplicantType = ApplicantType.CITIZEN
    city: str | None = None
    neighborhood: str | None = None
    zone_id: str | None = None
    preferred_language: str = "ar"


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=4, max_length=12)


class ResendOtpRequest(BaseModel):
    email: EmailStr


class UserRoleUpdateRequest(BaseModel):
    role: UserRole
    actor_id: str | None = None
    active: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class CurrentUser(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    actor_id: str | None = None
    active: bool = True
    email_verified: bool = True
    permissions: list[str] = Field(default_factory=list)

