from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings

_client: MongoClient | None = None
_db: Database | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri, uuidRepresentation="standard")
    return _client


def get_db() -> Database:
    global _db
    if _db is None:
        settings = get_settings()
        _db = get_client()[settings.mongodb_db]
    return _db


def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None

