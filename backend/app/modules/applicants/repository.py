from pymongo.errors import DuplicateKeyError

from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class ApplicantRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()
        self.collection = self.db.applicants

    def create(self, doc: dict) -> dict:
        try:
            self.collection.insert_one(doc)
        except DuplicateKeyError:
            return mongo_doc(self.collection.find_one({"identity.national_id": doc["identity"]["national_id"]}))
        return mongo_doc(self.collection.find_one({"applicant_id": doc["applicant_id"]}))

    def get(self, applicant_id: str) -> dict | None:
        return mongo_doc(self.collection.find_one({"applicant_id": applicant_id}))

    def get_by_national_id(self, national_id: str) -> dict | None:
        return mongo_doc(self.collection.find_one({"identity.national_id": national_id}))

    def add_application(self, applicant_id: str, application_id: str) -> None:
        self.collection.update_one(
            {"applicant_id": applicant_id},
            {
                "$addToSet": {"linked_applications": application_id},
                "$inc": {"stats.total_applications": 1, "stats.pending_applications": 1},
            },
        )

    def applications(self, applicant_id: str) -> list[dict]:
        return [mongo_doc(doc) for doc in self.db.land_applications.find({"applicant_ref.applicant_id": applicant_id})]
