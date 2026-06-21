from pymongo import ASCENDING

from app.db.mongo import get_db
from app.shared.serialization import mongo_doc


class SurveyRepository:
    def __init__(self, db=None) -> None:
        self.db = db if db is not None else get_db()

    def application(self, application_id: str) -> dict | None:
        return mongo_doc(self.db.land_applications.find_one({"application_id": application_id}))

    def existing_task(self, application_id: str) -> dict | None:
        return mongo_doc(self.db.survey_tasks.find_one({"application_id": application_id}))

    def candidates(self, zone_id: str) -> list[dict]:
        return [
            mongo_doc(doc)
            for doc in self.db.staff_members.find(
                {
                    "role": "surveyor",
                    "active": True,
                    "coverage.zone_ids": zone_id,
                    "$expr": {"$lt": ["$workload.active_tasks", "$workload.max_tasks"]},
                }
            )
        ]

    def create_task(self, task: dict, surveyor_code: str) -> dict:
        self.db.survey_tasks.insert_one(task)
        self.db.staff_members.update_one(
            {"staff_code": surveyor_code},
            {"$inc": {"workload.active_tasks": 1}, "$set": {"updated_at": task["created_at"]}},
        )
        self.db.land_applications.update_one(
            {"application_id": task["application_id"]},
            {
                "$set": {
                    "assignment.assigned_surveyor_id": surveyor_code,
                    "assignment.assignment_policy": "zone+workload+availability+skill+priority+existing_tasks",
                    "timestamps.updated_at": task["created_at"],
                }
            },
        )
        return mongo_doc(self.db.survey_tasks.find_one({"task_id": task["task_id"]}))

    def update_task_milestone(self, application_id: str, milestone: dict) -> dict | None:
        self.db.survey_tasks.update_one(
            {"application_id": application_id},
            {
                "$set": {"status": milestone["type"], "updated_at": milestone["at"]},
                "$push": {"milestones": milestone},
            },
        )
        return self.existing_task(application_id)

    def save_report(self, report: dict) -> dict:
        self.db.survey_reports.update_one({"application_id": report["application_id"]}, {"$set": report}, upsert=True)
        return mongo_doc(self.db.survey_reports.find_one({"application_id": report["application_id"]}))

    def set_application_status(self, application_id: str, status: str, now) -> None:
        self.db.land_applications.update_one(
            {"application_id": application_id},
            {
                "$set": {
                    "status": status,
                    "workflow.current_state": status,
                    f"timestamps.{status}_at": now,
                    "timestamps.updated_at": now,
                    "survey.report_uploaded": status == "surveyed",
                }
            },
        )

    def tasks(self, surveyor_id: str | None = None) -> list[dict]:
        query = {"assigned_surveyor_id": surveyor_id} if surveyor_id else {}
        return [mongo_doc(doc) for doc in self.db.survey_tasks.find(query).sort("created_at", ASCENDING)]
