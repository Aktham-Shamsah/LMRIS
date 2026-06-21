from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class RegistrarRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()

    def application(self, application_id: str) -> dict | None:
        return mongo_doc(self.db.land_applications.find_one({"application_id": application_id}))

    def survey_task(self, application_id: str) -> dict | None:
        return mongo_doc(self.db.survey_tasks.find_one({"application_id": application_id}))

    def update_application(self, application_id: str, update: dict, push: dict | None = None) -> dict | None:
        op = {"$set": update}
        if push:
            op["$push"] = push
        self.db.land_applications.update_one({"application_id": application_id}, op)
        return self.application(application_id)

    def mark_survey_registrar_reviewed(self, application_id: str, milestone: dict) -> None:
        self.db.survey_tasks.update_one(
            {"application_id": application_id},
            {"$set": {"status": "registrar_reviewed", "updated_at": milestone["at"]}, "$push": {"milestones": milestone}},
        )

    def resolve_objections(self, application_id: str, now) -> None:
        self.db.objections.update_many({"application_id": application_id, "status": "open"}, {"$set": {"status": "resolved", "resolved_at": now}})
