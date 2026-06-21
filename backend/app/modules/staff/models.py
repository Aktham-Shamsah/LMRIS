from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.shared.enums import StaffRole


class Coverage(BaseModel):
    zone_ids: list[str] = Field(default_factory=list)
    geo_fence: dict[str, Any] | None = None


class Workload(BaseModel):
    active_tasks: int = 0
    max_tasks: int = 10


class Contacts(BaseModel):
    phone: str | None = None
    email: EmailStr | None = None


class StaffCreate(BaseModel):
    staff_code: str | None = None
    name: str
    role: StaffRole
    department: str = "Land Registration"
    skills: list[str] = Field(default_factory=list)
    coverage: Coverage = Field(default_factory=Coverage)
    schedule: dict[str, Any] = Field(default_factory=lambda: {"timezone": "Asia/Jerusalem", "shifts": [], "on_call": False})
    workload: Workload = Field(default_factory=Workload)
    contacts: Contacts = Field(default_factory=Contacts)
    active: bool = True

