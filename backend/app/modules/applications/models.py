from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.shared.enums import ApplicantType, ApplicationStatus, ApplicationType, DocumentStatus


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: list[Any]

    @model_validator(mode="after")
    def validate_geojson(self):
        allowed = {"Point", "Polygon", "MultiPolygon", "LineString"}
        if self.type not in allowed:
            raise ValueError(f"Unsupported GeoJSON geometry type: {self.type}")
        if not self.coordinates:
            raise ValueError("GeoJSON coordinates are required.")
        return self


class ApplicantRef(BaseModel):
    applicant_id: str
    applicant_type: ApplicantType
    submitted_by_representative: bool = False


class ParcelRef(BaseModel):
    parcel_number: str
    block_number: str
    basin_number: str
    zone_id: str
    parcel_code: str | None = None
    parcel_id: str | None = None
    owner_refs: list[dict[str, Any]] = Field(default_factory=list)
    geometry: GeoJSONGeometry | None = None


class RequiredDocument(BaseModel):
    document_type: str
    required: bool = True
    status: DocumentStatus = DocumentStatus.MISSING


class ApplicationCreate(BaseModel):
    application_type: ApplicationType
    applicant_ref: ApplicantRef
    parcel_ref: ParcelRef
    description: str | None = None
    priority: str = "normal"
    tags: list[str] = Field(default_factory=list)
    required_documents: list[RequiredDocument] = Field(default_factory=list)
    idempotency_key: str | None = None


class TransitionRequest(BaseModel):
    target_status: ApplicationStatus | None = None
    new_status: ApplicationStatus | None = None
    reason: str | None = None
    performed_by: str = "staff"

    @property
    def selected_status(self) -> ApplicationStatus:
        target = self.target_status or self.new_status
        if target is None:
            raise ValueError("target_status is required.")
        return target


class ReasonRequest(BaseModel):
    reason: str
    performed_by: str = "staff"


class DocumentCreate(BaseModel):
    document_type: str
    filename: str
    content_type: str | None = None
    storage_url: str | None = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    uploaded_by: str = "applicant"
    is_ownership_doc: bool = False
    notes: str | None = None


class CommentCreate(BaseModel):
    text: str
    author_id: str
    author_type: str = "applicant"


class ObjectionCreate(BaseModel):
    reason: str
    submitted_by: str
    evidence_documents: list[dict[str, Any]] = Field(default_factory=list)

