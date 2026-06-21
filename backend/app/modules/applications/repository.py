from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class ApplicationRepository:
    SORTABLE = {
        "submitted_at": "timestamps.submitted_at",
        "updated_at": "timestamps.updated_at",
        "status": "status",
        "application_type": "application_type",
        "priority": "priority",
    }

    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()
        self.collection = self.db.land_applications

    def create(self, doc: dict) -> dict:
        try:
            self.collection.insert_one(doc)
        except DuplicateKeyError:
            if doc.get("idempotency_key"):
                existing = self.get_by_idempotency_key(doc["idempotency_key"])
                if existing:
                    return existing
            raise
        return mongo_doc(self.collection.find_one({"application_id": doc["application_id"]}))

    def get(self, application_id: str) -> dict | None:
        query: dict[str, Any] = {"application_id": application_id}
        if ObjectId.is_valid(application_id):
            query = {"$or": [{"application_id": application_id}, {"_id": ObjectId(application_id)}]}
        return mongo_doc(self.collection.find_one(query))

    def get_by_idempotency_key(self, key: str) -> dict | None:
        return mongo_doc(self.collection.find_one({"idempotency_key": key}))

    def list(
        self,
        page: int,
        limit: int,
        status: str | None = None,
        application_type: str | None = None,
        zone_id: str | None = None,
        dispute_state: str | None = None,
        search: str | None = None,
        sort_by: str = "submitted_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict], int]:
        query: dict[str, Any] = {}
        if status:
            query["status"] = status
        if application_type:
            query["application_type"] = application_type
        if zone_id:
            query["parcel_ref.zone_id"] = zone_id
        if dispute_state:
            query["parcel_ref.dispute_state"] = dispute_state
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [
                {"application_id": pattern},
                {"parcel_ref.parcel_number": pattern},
                {"parcel_ref.parcel_code": pattern},
                {"applicant_ref.applicant_id": pattern},
            ]
        total = self.collection.count_documents(query)
        direction = ASCENDING if sort_order == "asc" else DESCENDING
        sort_field = self.SORTABLE.get(sort_by, "timestamps.submitted_at")
        cursor = self.collection.find(query).sort(sort_field, direction).skip((page - 1) * limit).limit(limit)
        return [mongo_doc(doc) for doc in cursor], total

    def update(self, application_id: str, update: dict, push: dict | None = None) -> dict | None:
        operation: dict[str, Any] = {"$set": update}
        if push:
            operation["$push"] = push
        self.collection.update_one({"application_id": application_id}, operation)
        return self.get(application_id)

    def upsert_parcel(self, parcel: dict) -> dict:
        self.db.parcels.update_one({"parcel_code": parcel["parcel_code"]}, {"$set": parcel}, upsert=True)
        return mongo_doc(self.db.parcels.find_one({"parcel_code": parcel["parcel_code"]}))

    def add_document(self, application_id: str, document: dict) -> dict:
        self.db.application_documents.insert_one(document)
        summary = {
            "document_id": document["document_id"],
            "document_type": document["document_type"],
            "filename": document["filename"],
            "status": document["status"],
            "uploaded_at": document["uploaded_at"],
            "is_ownership_doc": document.get("is_ownership_doc", False),
        }
        self.collection.update_one(
            {"application_id": application_id},
            {
                "$push": {"documents": summary},
                "$set": {"timestamps.updated_at": document["uploaded_at"]},
            },
        )
        return mongo_doc(document)

    def get_documents(self, application_id: str) -> list[dict]:
        return [mongo_doc(doc) for doc in self.db.application_documents.find({"application_id": application_id})]

    def add_comment(self, application_id: str, comment: dict) -> dict:
        self.collection.update_one(
            {"application_id": application_id},
            {"$push": {"comments": comment}, "$set": {"timestamps.updated_at": comment["created_at"]}},
        )
        return mongo_doc(comment)

    def add_objection(self, application_id: str, objection: dict) -> dict:
        self.db.objections.insert_one(objection)
        self.collection.update_one(
            {"application_id": application_id},
            {
                "$set": {
                    "status": "under_objection",
                    "workflow.current_state": "under_objection",
                    "objection.has_objection": True,
                    "timestamps.updated_at": objection["submitted_at"],
                },
                "$push": {"objection.objection_ids": objection["objection_id"]},
            },
        )
        return mongo_doc(objection)

    def get_objections(self, application_id: str) -> list[dict]:
        return [mongo_doc(doc) for doc in self.db.objections.find({"application_id": application_id})]

    def has_survey_report(self, application_id: str) -> bool:
        return self.db.survey_reports.count_documents({"application_id": application_id}) > 0

    def has_ownership_documents(self, application_id: str) -> bool:
        return (
            self.db.application_documents.count_documents(
                {
                    "application_id": application_id,
                    "$or": [{"is_ownership_doc": True}, {"document_type": {"$in": ["ownership_deed", "sale_contract", "title_deed"]}}],
                    "status": {"$in": ["uploaded", "pending_review", "verified"]},
                }
            )
            > 0
        )

    def save_certificate(self, certificate: dict) -> dict:
        self.db.certificates.insert_one(certificate)
        return mongo_doc(self.db.certificates.find_one({"certificate_id": certificate["certificate_id"]}))

    def latest_certificate(self, application_id: str) -> dict | None:
        return mongo_doc(self.db.certificates.find_one({"application_id": application_id}, sort=[("issued_at", DESCENDING)]))
