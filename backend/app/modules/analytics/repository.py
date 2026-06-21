from app.db.mongo import get_db
from app.shared.serialization import serialize


class AnalyticsRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()

    def aggregate(self, collection_name: str, pipeline: list[dict]) -> list[dict]:
        return serialize(list(self.db[collection_name].aggregate(pipeline)))

    def parcels(self, query: dict) -> list[dict]:
        return serialize(list(self.db.parcels.find(query)))
