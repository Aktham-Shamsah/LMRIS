from typing import Optional
from fastapi import APIRouter, Query, Body, HTTPException, status
from schemas.parcel import (
    ParcelCreate, ParcelUpdate, ParcelResponse, ParcelListResponse, NearbyQuery,
    validate_polygon_coordinates,
)
from schemas.common import APIResponse, PaginationParams
from services.parcel_service import ParcelService

router = APIRouter(prefix="/parcels", tags=["Parcels"])
_svc = ParcelService()


@router.post(
    "",
    response_model=APIResponse[ParcelResponse],
    status_code=201,
    summary="Register a new parcel",
)
def create_parcel(payload: ParcelCreate):
    return APIResponse(data=_svc.create(payload), message="Parcel registered.")


@router.get(
    "",
    response_model=APIResponse[ParcelListResponse],
    summary="List parcels with optional filters",
)
def list_parcels(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    zone_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    params = PaginationParams(page=page, limit=limit)
    items, total = _svc.list(skip=params.skip, limit=params.limit, zone_id=zone_id, status_filter=status)
    return APIResponse(data=ParcelListResponse(total=total, page=page, limit=limit, items=items))


@router.get(
    "/nearby",
    response_model=APIResponse[list[ParcelResponse]],
    summary="Find parcels near a coordinate (2dsphere $near query)",
)
def find_nearby(
    longitude: float = Query(..., ge=-180, le=180),
    latitude: float = Query(..., ge=-90, le=90),
    max_distance_meters: float = Query(default=5000, gt=0, le=500_000),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = NearbyQuery(longitude=longitude, latitude=latitude,
                        max_distance_meters=max_distance_meters, limit=limit)
    return APIResponse(data=_svc.find_nearby(query))


@router.post(
    "/within-polygon",
    response_model=APIResponse[list[ParcelResponse]],
    summary="Find parcels within a GeoJSON polygon (2dsphere $geoWithin)",
)
def find_within_polygon(
    coordinates: list = Body(
        ...,
        description="GeoJSON polygon coordinates array, e.g. [[[lng,lat], [lng,lat], ...]]",
        examples=[[[[35.2, 31.9], [35.3, 31.9], [35.3, 32.0], [35.2, 32.0], [35.2, 31.9]]]],
    )
):
    try:
        coordinates = validate_polygon_coordinates(coordinates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return APIResponse(data=_svc.find_within_polygon(coordinates))


@router.get(
    "/{parcel_id}",
    response_model=APIResponse[ParcelResponse],
    summary="Get parcel by ID",
)
def get_parcel(parcel_id: str):
    return APIResponse(data=_svc.get(parcel_id))


@router.patch(
    "/{parcel_id}",
    response_model=APIResponse[ParcelResponse],
    summary="Update parcel details",
)
def update_parcel(parcel_id: str, payload: ParcelUpdate):
    return APIResponse(data=_svc.update(parcel_id, payload), message="Parcel updated.")


@router.delete(
    "/{parcel_id}",
    response_model=APIResponse[None],
    summary="Delete a parcel",
)
def delete_parcel(parcel_id: str):
    _svc.delete(parcel_id)
    return APIResponse(message="Parcel deleted.")
