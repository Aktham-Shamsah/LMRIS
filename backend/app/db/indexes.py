from pymongo import ASCENDING, GEOSPHERE


def create_indexes(db) -> None:
    db.land_applications.create_index("application_id", unique=True)
    db.land_applications.create_index("status")
    db.land_applications.create_index("application_type")
    db.land_applications.create_index("parcel_ref.parcel_number")
    db.land_applications.create_index("parcel_ref.zone_id")
    db.land_applications.create_index("timestamps.submitted_at")

    db.parcels.create_index("parcel_code", unique=True)
    db.parcels.create_index([("geometry", GEOSPHERE)])
    db.parcels.create_index("zone_id")

    db.applicants.create_index("identity.national_id", unique=True)
    db.staff_members.create_index("staff_code", unique=True)
    db.survey_tasks.create_index("application_id")
    db.certificates.create_index("certificate_id", unique=True)

    db.land_applications.create_index("idempotency_key", unique=True, sparse=True)
    db.land_applications.create_index([("status", ASCENDING), ("parcel_ref.zone_id", ASCENDING)])
    db.land_applications.create_index([("objection.has_objection", ASCENDING), ("status", ASCENDING)])
    db.application_documents.create_index("application_id")
    db.application_documents.create_index([("application_id", ASCENDING), ("document_type", ASCENDING)])
    db.application_documents.create_index("status")
    db.objections.create_index("application_id")
    db.objections.create_index([("application_id", ASCENDING), ("status", ASCENDING)])
    db.performance_logs.create_index("application_id", unique=True)
    db.performance_logs.create_index("event_stream.type")
    db.performance_logs.create_index("event_stream.at")
    db.survey_reports.create_index("application_id", unique=True)
    db.survey_tasks.create_index([("assigned_surveyor_id", ASCENDING), ("status", ASCENDING)])

