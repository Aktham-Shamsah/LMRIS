from typing import Any

from pydantic import BaseModel, Field

from app.shared.enums import SurveyMilestone


class SurveyMilestoneRequest(BaseModel):
    milestone: SurveyMilestone
    by: str = "surveyor"
    meta: dict[str, Any] = Field(default_factory=dict)


class SurveyReportCreate(BaseModel):
    report_title: str
    surveyor_id: str
    findings: str
    evidence_files: list[dict[str, Any]] = Field(default_factory=list)
    field_notes: list[str] = Field(default_factory=list)

