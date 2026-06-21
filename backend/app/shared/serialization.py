from datetime import date, datetime
from typing import Any

from bson import ObjectId


def serialize(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


def mongo_doc(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    return serialize(doc)

