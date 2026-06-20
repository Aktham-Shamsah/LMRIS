from __future__ import annotations
from pymongo import MongoClient
from pymongo.database import Database
from config import get_settings

settings = get_settings()

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
        )
    return _client


def get_db() -> Database:
    return get_client()[settings.mongo_db_name]


db: Database = get_db()
