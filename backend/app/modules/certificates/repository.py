from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class CertificateRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()
        self.collection = self.db.certificates

    def get(self, certificate_id: str) -> dict | None:
        return mongo_doc(self.collection.find_one({"certificate_id": certificate_id}))

    def by_application(self, application_id: str) -> dict | None:
        return mongo_doc(self.collection.find_one({"application_id": application_id}, sort=[("issued_at", -1)]))
