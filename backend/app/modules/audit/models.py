from typing import Any

from pydantic import BaseModel, Field


class AuditActor(BaseModel):
    actor_type: str = "system"
    actor_id: str = "system"


class AuditEvent(BaseModel):
    type: str
    by: AuditActor = Field(default_factory=AuditActor)
    at: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

