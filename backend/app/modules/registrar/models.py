from typing import Literal

from pydantic import BaseModel


RegistrarDecision = Literal["accept", "approve", "hold", "reject", "request_documents", "continue_after_objection"]


class RegistrarReviewRequest(BaseModel):
    decision: RegistrarDecision
    registrar_id: str
    notes: str | None = None
    reason: str | None = None

