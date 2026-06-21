from __future__ import annotations
from typing import Optional
from pymongo.collection import Collection
from database.connection import db
from models.audit_log import AuditLogModel


class AuditRepository:
    def __init__(self) -> None:
        self._col: Collection = db[AuditLogModel.collection_name]

    def _s(self, doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if entity_id:
            query["entity_id"] = entity_id
        if action:
            query["action"] = action
        total = self._col.count_documents(query)
        cursor = self._col.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        return [self._s(d) for d in cursor], total
