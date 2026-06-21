from __future__ import annotations
from typing import Optional
from fastapi import HTTPException, status
from repositories.parcel_repository import ParcelRepository
from models.parcel import ParcelModel
from schemas.parcel import ParcelCreate, ParcelUpdate, NearbyQuery


class ParcelService:
    def __init__(self) -> None:
        self._repo = ParcelRepository()

    def create(self, payload: ParcelCreate) -> dict:
        if self._repo.get_by_code(payload.parcel_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Parcel code '{payload.parcel_code}' already exists.",
            )
        doc = ParcelModel.new(
            parcel_code=payload.parcel_code,
            parcel_number=payload.parcel_number,
            zone_id=payload.zone_id,
            owner=payload.owner.model_dump(),
            area=payload.area,
            geometry=payload.geometry.model_dump(),
            land_use=payload.land_use,
            description=payload.description,
            status=payload.status,
        )
        return self._repo.create(doc)

    def get(self, parcel_id: str) -> dict:
        parcel = self._repo.get_by_id(parcel_id)
        if not parcel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found.")
        return parcel

    def list(
        self,
        skip: int,
        limit: int,
        zone_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        return self._repo.list(skip=skip, limit=limit, zone_id=zone_id, status=status_filter)

    def update(self, parcel_id: str, payload: ParcelUpdate) -> dict:
        self.get(parcel_id)
        fields = payload.model_dump(exclude_none=True)
        if "owner" in fields and payload.owner:
            fields["owner"] = payload.owner.model_dump()
        if "geometry" in fields and payload.geometry:
            fields["geometry"] = payload.geometry.model_dump()
        updated = self._repo.update(parcel_id, fields)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found.")
        return updated

    def delete(self, parcel_id: str) -> None:
        self.get(parcel_id)
        if not self._repo.delete(parcel_id):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Delete failed.")

    def find_nearby(self, query: NearbyQuery) -> list[dict]:
        return self._repo.find_nearby(
            longitude=query.longitude,
            latitude=query.latitude,
            max_dist=query.max_distance_meters,
            limit=query.limit,
        )

    def find_within_polygon(self, coordinates: list) -> list[dict]:
        return self._repo.find_within_polygon(coordinates)
