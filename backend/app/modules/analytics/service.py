from app.modules.analytics.repository import AnalyticsRepository


PENDING_STATUSES = ["submitted", "pre_checked", "survey_required", "surveyed", "legal_review", "missing_documents", "under_objection", "on_hold"]


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository | None = None) -> None:
        self.repo = repo or AnalyticsRepository()

    def kpis(self) -> dict:
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "pending": [{"$match": {"status": {"$in": PENDING_STATUSES}}}, {"$count": "count"}],
                    "approved": [{"$match": {"status": "approved"}}, {"$count": "count"}],
                    "rejected": [{"$match": {"status": "rejected"}}, {"$count": "count"}],
                    "under_objection": [{"$match": {"status": "under_objection"}}, {"$count": "count"}],
                    "by_type": [{"$group": {"_id": "$application_type", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}],
                }
            }
        ]
        result = self.repo.aggregate("land_applications", pipeline)
        data = result[0] if result else {}

        def first_count(key: str) -> int:
            values = data.get(key) or []
            return values[0]["count"] if values else 0

        certs = self.repo.aggregate(
            "certificates",
            [
                {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$issued_at"}}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
        )
        return {
            "total_applications": first_count("total"),
            "pending_applications": first_count("pending"),
            "approved_applications": first_count("approved"),
            "rejected_applications": first_count("rejected"),
            "applications_under_objection": first_count("under_objection"),
            "applications_by_type": data.get("by_type", []),
            "certificates_issued_per_month": certs,
        }

    def applications_by_status(self) -> list[dict]:
        return self.repo.aggregate("land_applications", [{"$group": {"_id": "$status", "count": {"$sum": 1}}}, {"$sort": {"_id": 1}}])

    def applications_by_zone(self) -> list[dict]:
        return self.repo.aggregate(
            "land_applications",
            [
                {"$group": {"_id": "$parcel_ref.zone_id", "count": {"$sum": 1}, "under_objection": {"$sum": {"$cond": [{"$eq": ["$status", "under_objection"]}, 1, 0]}}}},
                {"$sort": {"count": -1}},
            ],
        )

    def processing_time(self) -> dict:
        pipeline = [
            {
                "$project": {
                    "application_type": 1,
                    "processing_days": {
                        "$cond": [
                            {"$and": ["$timestamps.closed_at", "$timestamps.submitted_at"]},
                            {"$divide": [{"$subtract": ["$timestamps.closed_at", "$timestamps.submitted_at"]}, 86400000]},
                            None,
                        ]
                    },
                }
            },
            {
                "$facet": {
                    "by_type": [
                        {"$match": {"processing_days": {"$ne": None}}},
                        {"$group": {"_id": "$application_type", "avg_days": {"$avg": "$processing_days"}, "count": {"$sum": 1}}},
                        {"$sort": {"avg_days": 1}},
                    ],
                    "buckets": [
                        {"$match": {"processing_days": {"$ne": None}}},
                        {"$bucketAuto": {"groupBy": "$processing_days", "buckets": 5, "output": {"count": {"$sum": 1}}}},
                    ],
                }
            },
        ]
        result = self.repo.aggregate("land_applications", pipeline)
        return result[0] if result else {"by_type": [], "buckets": []}

    def surveyors(self) -> list[dict]:
        return self.repo.aggregate(
            "staff_members",
            [
                {"$match": {"role": "surveyor"}},
                {"$lookup": {"from": "survey_tasks", "localField": "staff_code", "foreignField": "assigned_surveyor_id", "as": "tasks"}},
                {
                    "$project": {
                        "staff_code": 1,
                        "name": 1,
                        "coverage": 1,
                        "workload": 1,
                        "task_count": {"$size": "$tasks"},
                        "completed": {
                            "$size": {
                                "$filter": {"input": "$tasks", "as": "task", "cond": {"$eq": ["$$task.status", "registrar_reviewed"]}}
                            }
                        },
                    }
                },
                {"$sort": {"task_count": -1}},
            ],
        )

    def registrars(self) -> list[dict]:
        return self.repo.aggregate(
            "staff_members",
            [
                {"$match": {"role": "registrar"}},
                {"$lookup": {"from": "land_applications", "localField": "staff_code", "foreignField": "assignment.assigned_registrar_id", "as": "applications"}},
                {"$unwind": {"path": "$applications", "preserveNullAndEmptyArrays": True}},
                {"$group": {"_id": "$staff_code", "name": {"$first": "$name"}, "review_count": {"$sum": {"$cond": ["$applications", 1, 0]}}}},
                {"$sort": {"review_count": -1}},
            ],
        )

    def parcel_geofeed(self, zone_id: str | None = None, status: str | None = None, application_type: str | None = None, dispute_state: str | None = None) -> dict:
        query = {}
        if zone_id:
            query["zone_id"] = zone_id
        if dispute_state:
            query["dispute_state"] = dispute_state
        features = []
        for parcel in self.repo.parcels(query):
            app_query = {"parcel_ref.parcel_code": parcel.get("parcel_code")}
            if status:
                app_query["status"] = status
            if application_type:
                app_query["application_type"] = application_type
            applications = self.repo.aggregate("land_applications", [{"$match": app_query}, {"$project": {"_id": 0, "application_id": 1, "status": 1, "application_type": 1}}])
            features.append(
                {
                    "type": "Feature",
                    "geometry": parcel.get("geometry"),
                    "properties": {
                        "parcel_code": parcel.get("parcel_code"),
                        "zone_id": parcel.get("zone_id"),
                        "parcel_number": parcel.get("parcel_number"),
                        "dispute_state": parcel.get("dispute_state", "none"),
                        "applications": applications,
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}

    def pending_heatmap(self, longitude: float | None = None, latitude: float | None = None) -> dict:
        if longitude is not None and latitude is not None:
            pipeline = [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [longitude, latitude]},
                        "distanceField": "distance_m",
                        "spherical": True,
                    }
                },
                {"$lookup": {"from": "land_applications", "localField": "parcel_code", "foreignField": "parcel_ref.parcel_code", "as": "applications"}},
                {"$unwind": "$applications"},
                {"$match": {"applications.status": {"$in": PENDING_STATUSES}}},
                {"$project": {"parcel_code": 1, "zone_id": 1, "geometry": 1, "distance_m": 1, "application_id": "$applications.application_id", "status": "$applications.status"}},
                {"$sort": {"distance_m": 1}},
            ]
            docs = self.repo.aggregate("parcels", pipeline)
        else:
            pipeline = [
                {"$match": {"status": {"$in": PENDING_STATUSES}}},
                {"$lookup": {"from": "parcels", "localField": "parcel_ref.parcel_code", "foreignField": "parcel_code", "as": "parcel"}},
                {"$unwind": "$parcel"},
                {"$project": {"application_id": 1, "status": 1, "zone_id": "$parcel.zone_id", "geometry": "$parcel.geometry", "parcel_code": "$parcel.parcel_code"}},
                {"$sort": {"zone_id": 1}},
            ]
            docs = self.repo.aggregate("land_applications", pipeline)
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": doc.get("geometry"),
                    "properties": {key: value for key, value in doc.items() if key not in {"geometry", "_id"}},
                }
                for doc in docs
            ],
        }
