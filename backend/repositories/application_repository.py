from __future__ import annotations
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from database.connection import db
from models.application import ApplicationModel


class ApplicationRepository:
    SORTABLE_FIELDS = {
        "created_at": "timestamps.created_at",
        "updated_at": "timestamps.updated_at",
        "submitted_at": "timestamps.submitted_at",
        "completed_at": "timestamps.completed_at",
        "status": "status",
        "application_type": "application_type",
    }

    def __init__(self) -> None:
        self._col: Collection = db[ApplicationModel.collection_name]

    def _s(self, doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def create(self, doc: dict) -> dict:
        result = self._col.insert_one(doc)
        return self._s(self._col.find_one({"_id": result.inserted_id}))

    def get_by_id(self, app_id: str) -> Optional[dict]:
        try:
            doc = self._col.find_one({"_id": ObjectId(app_id)})
        except Exception:
            return None
        return self._s(doc) if doc else None

    def get_by_application_id(self, application_id: str) -> Optional[dict]:
        doc = self._col.find_one({"application_id": application_id})
        return self._s(doc) if doc else None

    def get_by_idempotency_key(self, key: str) -> Optional[dict]:
        doc = self._col.find_one({"idempotency_key": key})
        return self._s(doc) if doc else None

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        application_type: Optional[str] = None,
        zone_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if status:
            query["status"] = status
        if application_type:
            query["application_type"] = application_type
        if zone_id:
            query["parcel_ref.zone_id"] = zone_id
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [
                {"application_id": pattern},
                {"applicant.name": pattern},
                {"applicant.email": pattern},
                {"applicant.national_id": pattern},
                {"parcel_ref.parcel_code": pattern},
            ]

        total = self._col.count_documents(query)
        sort_field = self.SORTABLE_FIELDS.get(sort_by, "timestamps.created_at")
        direction = ASCENDING if sort_order == "asc" else DESCENDING
        cursor = (
            self._col.find(query)
            .sort(sort_field, direction)
            .skip(skip)
            .limit(limit)
        )
        return [self._s(d) for d in cursor], total

    def update_fields(self, app_id: str, fields: dict) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {"$set": fields},
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def place_on_hold(self, app_id: str, fields: dict, history_entry: dict) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {
                    "$set": fields,
                    "$push": {"hold_history": history_entry},
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def reject(self, app_id: str, fields: dict, history_entry: dict) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {
                    "$set": fields,
                    "$push": {"rejection_history": history_entry},
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def add_document(self, app_id: str, attachment: dict) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {
                    "$push": {"documents": attachment},
                    "$set": {"timestamps.updated_at": datetime.now(timezone.utc)},
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def verify_document(self, app_id: str, doc_id: str, performed_by: str = "system") -> Optional[dict]:
        now = datetime.now(timezone.utc)
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id), "documents.doc_id": doc_id},
                {
                    "$set": {
                        "documents.$.verified": True,
                        "documents.$.verified_at": now,
                        "documents.$.verified_by": performed_by,
                        "timestamps.updated_at": now,
                    }
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def set_survey_report(self, app_id: str, report: dict) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {
                    "$set": {
                        "survey.report": report,
                        "timestamps.updated_at": datetime.now(timezone.utc),
                    }
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def add_note(self, app_id: str, note: dict) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {
                    "$push": {"internal_notes": note},
                    "$set": {"timestamps.updated_at": datetime.now(timezone.utc)},
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def remove_document(self, app_id: str, doc_id: str) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(app_id)},
                {
                    "$pull": {"documents": {"doc_id": doc_id}},
                    "$set": {"timestamps.updated_at": datetime.now(timezone.utc)},
                },
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None

    def delete(self, app_id: str) -> bool:
        try:
            result = self._col.delete_one({"_id": ObjectId(app_id)})
        except Exception:
            return False
        return result.deleted_count == 1
