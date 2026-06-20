from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo


ParcelStatus = Literal["active", "inactive", "under_transfer", "subdivided"]


def _validate_lng_lat(pair) -> list[float]:
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ValueError(f"Each coordinate must be [longitude, latitude], got {pair!r}.")
    lng, lat = pair
    if isinstance(lng, bool) or isinstance(lat, bool) or not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
        raise ValueError(f"Longitude/latitude must be numbers, got {pair!r}.")
    if not (-180 <= lng <= 180):
        raise ValueError(f"Longitude {lng} is out of bounds (must be between -180 and 180).")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} is out of bounds (must be between -90 and 90).")
    return [float(lng), float(lat)]


def _validate_ring(ring) -> list[list[float]]:
    if not isinstance(ring, list) or len(ring) < 4:
        raise ValueError("Each polygon ring needs at least 4 coordinate pairs and must be closed.")
    points = [_validate_lng_lat(pt) for pt in ring]
    if points[0] != points[-1]:
        raise ValueError("Each polygon ring must be closed (first and last coordinate pairs must match).")
    return points


def validate_polygon_coordinates(coordinates) -> list:
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Polygon coordinates must be a non-empty list of linear rings.")
    return [_validate_ring(ring) for ring in coordinates]


class OwnerSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    national_id: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(default="", max_length=30)


class GeoJsonGeometry(BaseModel):
    type: Literal["Point", "Polygon", "MultiPolygon"]
    coordinates: list  # flexible to accept both Point [lng,lat] and Polygon [[[lng,lat],...]]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v, info: ValidationInfo):
        geo_type = info.data.get("type")
        if geo_type == "Point":
            return _validate_lng_lat(v)
        if geo_type == "Polygon":
            return validate_polygon_coordinates(v)
        if geo_type == "MultiPolygon":
            if not isinstance(v, list) or not v:
                raise ValueError("MultiPolygon coordinates must be a non-empty list of polygons.")
            return [validate_polygon_coordinates(p) for p in v]
        return v


class ParcelCreate(BaseModel):
    parcel_code: str = Field(..., min_length=1, max_length=50, description="Unique parcel code")
    parcel_number: str = Field(..., min_length=1, max_length=50)
    zone_id: str = Field(..., min_length=1, max_length=50)
    owner: OwnerSchema
    area: float = Field(..., gt=0, description="Area in square meters")
    geometry: GeoJsonGeometry = Field(..., description="GeoJSON geometry (Point or Polygon)")
    land_use: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=2000)
    status: ParcelStatus = "active"


class ParcelUpdate(BaseModel):
    owner: Optional[OwnerSchema] = None
    area: Optional[float] = Field(default=None, gt=0)
    geometry: Optional[GeoJsonGeometry] = None
    land_use: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[ParcelStatus] = None


class ParcelResponse(BaseModel):
    id: str
    parcel_code: str
    parcel_number: str
    zone_id: str
    owner: OwnerSchema
    area: float
    geometry: GeoJsonGeometry
    land_use: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class ParcelListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[ParcelResponse]


class NearbyQuery(BaseModel):
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    max_distance_meters: float = Field(default=5000, gt=0, le=500_000)
    limit: int = Field(default=20, ge=1, le=100)
