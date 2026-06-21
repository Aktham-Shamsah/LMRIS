from __future__ import annotations
from typing import Optional
from bson import ObjectId
from pymongo.collection import Collection
from database.connection import db
from models.certificate import CertificateModel


class CertificateRepository:
    def __init__(self) -> None:
        self._col: Collection = db[CertificateModel.collection_name]

    def _s(self, doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def create(self, doc: dict) -> dict:
        result = self._col.insert_one(doc)
        return self._s(self._col.find_one({"_id": result.inserted_id}))

    def get_by_id(self, cert_id: str) -> Optional[dict]:
        try:
            doc = self._col.find_one({"_id": ObjectId(cert_id)})
        except Exception:
            return None
        return self._s(doc) if doc else None

    def get_by_certificate_id(self, certificate_id: str) -> Optional[dict]:
        doc = self._col.find_one({"certificate_id": certificate_id})
        return self._s(doc) if doc else None

    def get_latest_by_application_id(self, application_id: str) -> Optional[dict]:
        doc = self._col.find_one({"application_id": application_id}, sort=[("issued_at", -1)])
        return self._s(doc) if doc else None

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        parcel_code: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if parcel_code:
            query["parcel_code"] = parcel_code
        total = self._col.count_documents(query)
        cursor = self._col.find(query).sort("issued_at", -1).skip(skip).limit(limit)
        return [self._s(d) for d in cursor], total

    def revoke(self, cert_id: str) -> Optional[dict]:
        try:
            doc = self._col.find_one_and_update(
                {"_id": ObjectId(cert_id)},
                {"$set": {"status": "revoked"}},
                return_document=True,
            )
        except Exception:
            return None
        return self._s(doc) if doc else None
