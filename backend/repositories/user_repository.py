from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pymongo.collection import Collection
from database.connection import db
from models.user import UserModel


class UserRepository:
    def __init__(self) -> None:
        self._col: Collection = db[UserModel.collection_name]

    def _serialize(self, doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def create(self, doc: dict) -> dict:
        result = self._col.insert_one(doc)
        return self._serialize(self._col.find_one({"_id": result.inserted_id}))

    def get_by_id(self, user_id: str) -> Optional[dict]:
        try:
            doc = self._col.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
        return self._serialize(doc) if doc else None

    def get_by_email(self, email: str) -> Optional[dict]:
        doc = self._col.find_one({"email": email})
        return self._serialize(doc) if doc else None

    def list(self, skip: int = 0, limit: int = 20) -> tuple[list[dict], int]:
        total = self._col.count_documents({})
        cursor = self._col.find().skip(skip).limit(limit).sort("created_at", -1)
        return [self._serialize(d) for d in cursor], total

    def update(self, user_id: str, updates: dict) -> Optional[dict]:
        updates["updated_at"] = datetime.now(timezone.utc)
        try:
            result = self._col.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": updates},
                return_document=True,
            )
        except Exception:
            return None
        return self._serialize(result) if result else None

    def delete(self, user_id: str) -> bool:
        try:
            result = self._col.delete_one({"_id": ObjectId(user_id)})
        except Exception:
            return False
        return result.deleted_count == 1
