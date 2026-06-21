from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class AuditRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()
        self.collection = self.db.performance_logs

    def append_event(self, application_id: str, event: dict) -> dict:
        self.collection.update_one(
            {"application_id": application_id},
            {
                "$setOnInsert": {
                    "application_id": application_id,
                    "computed_kpis": {
                        "processing_days": None,
                        "precheck_minutes": None,
                        "survey_delay_days": None,
                        "certificate_issued": False,
                    },
                },
                "$push": {"event_stream": event},
            },
            upsert=True,
        )
        return mongo_doc(self.collection.find_one({"application_id": application_id}))

    def get_timeline(self, application_id: str) -> list[dict]:
        doc = self.collection.find_one({"application_id": application_id}) or {}
        return mongo_doc(doc.get("event_stream", []))
