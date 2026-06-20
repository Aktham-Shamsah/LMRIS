from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pymongo.collection import Collection
from database.connection import db
from models.parcel import ParcelModel


class ParcelRepository:
    def __init__(self) -> None:
        self._col: Collection = db[ParcelModel.collection_name]

    def _s(self, doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def create(self, doc: dict) -> dict:
        result = self._col.insert_one(doc)
        return self._s(self._col.find_one({"_id": result.inserted_id}))

    def get_by_id(self, parcel_id: str) -> Optional[dict]:
        try:
            doc = self._col.find_one({"_id": ObjectId(parcel_id)})
        except Exception:
            return None
        return self._s(doc) if doc else None

    def get_by_code(self, parcel_code: str) -> Optional[dict]:
        doc = self._col.find_one({"parcel_code": parcel_code})
        return self._s(doc) if doc else None

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        zone_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if zone_id:
            query["zone_id"] = zone_id
        if status:
            query["status"] = status
        total = self._col.count_documents(query)
        cursor = self._col.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return [self._s(d) for d in cursor], total

    def update(self, parcel_id: str, fields: dict) -> Optional[dict]:
        fields["updated_at"] = datetime.now(timezone.utc)
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(parcel_id)},
                {"$set": fields},
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def delete(self, parcel_id: str) -> bool:
        try:
            result = self._col.delete_one({"_id": ObjectId(parcel_id)})
        except Exception:
            return False
        return result.deleted_count == 1

    def find_nearby(self, longitude: float, latitude: float, max_dist: float, limit: int) -> list[dict]:
        cursor = self._col.find(
            {
                "geometry": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                        "$maxDistance": max_dist,
                    }
                }
            }
        ).limit(limit)
        return [self._s(d) for d in cursor]

    def find_within_polygon(self, coordinates: list) -> list[dict]:
        cursor = self._col.find(
            {
                "geometry": {
                    "$geoWithin": {
                        "$geometry": {"type": "Polygon", "coordinates": coordinates}
                    }
                }
            }
        )
        return [self._s(d) for d in cursor]
