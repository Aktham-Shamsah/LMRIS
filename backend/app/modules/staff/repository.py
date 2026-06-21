from pymongo.errors import DuplicateKeyError

from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class StaffRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()
        self.collection = self.db.staff_members

    def create(self, doc: dict) -> dict:
        try:
            self.collection.insert_one(doc)
        except DuplicateKeyError:
            return mongo_doc(self.collection.find_one({"staff_code": doc["staff_code"]}))
        return mongo_doc(self.collection.find_one({"staff_code": doc["staff_code"]}))

    def get(self, staff_id: str) -> dict | None:
        return mongo_doc(self.collection.find_one({"$or": [{"staff_id": staff_id}, {"staff_code": staff_id}]}))

    def count_by_role(self, role: str) -> int:
        return self.collection.count_documents({"role": role})

    def workload_summary(self, staff_id: str) -> dict:
        tasks = list(self.db.survey_tasks.find({"assigned_surveyor_id": staff_id}))
        return {
            "active_survey_tasks": len([task for task in tasks if task.get("status") != "registrar_reviewed"]),
            "completed_survey_tasks": len([task for task in tasks if task.get("status") == "registrar_reviewed"]),
            "tasks": [mongo_doc(task) for task in tasks],
        }
