from pymongo import ASCENDING, DESCENDING, GEOSPHERE
from database.connection import db


def ensure_indexes() -> None:
    """Create all collection indexes on startup, including 2dsphere for geospatial queries."""

    # --- land_applications ---
    apps = db["land_applications"]
    apps.create_index([("application_id", ASCENDING)], unique=True, name="application_id_unique")
    apps.create_index([("status", ASCENDING)], name="app_status_asc")
    apps.create_index([("application_type", ASCENDING)], name="application_type_asc")
    apps.create_index([("parcel_ref.parcel_number", ASCENDING)], name="parcel_ref_number_asc")
    apps.create_index([("parcel_ref.zone_id", ASCENDING)], name="parcel_ref_zone_asc")
    apps.create_index([("timestamps.submitted_at", DESCENDING)], name="submitted_at_desc")
    apps.create_index([("timestamps.created_at", DESCENDING)], name="created_at_desc")
    apps.create_index([("timestamps.updated_at", DESCENDING)], name="updated_at_desc")
    apps.create_index(
        [("idempotency_key", ASCENDING)],
        unique=True,
        sparse=True,
        name="idempotency_key_unique",
    )

    # --- parcels ---
    parcels = db["parcels"]
    parcels.create_index([("parcel_code", ASCENDING)], unique=True, name="parcel_code_unique")
    parcels.create_index([("geometry", GEOSPHERE)], name="geometry_2dsphere")
    parcels.create_index([("zone_id", ASCENDING)], name="zone_id_asc")
    parcels.create_index([("status", ASCENDING)], name="parcel_status_asc")

    # --- certificates ---
    certs = db["certificates"]
    certs.create_index([("certificate_id", ASCENDING)], unique=True, name="certificate_id_unique")
    certs.create_index([("application_id", ASCENDING)], name="cert_application_id_asc")
    certs.create_index([("parcel_code", ASCENDING)], name="cert_parcel_code_asc")

    # --- performance_logs ---
    logs = db["performance_logs"]
    logs.create_index([("timestamp", DESCENDING)], name="log_timestamp_desc")
    logs.create_index([("entity_id", ASCENDING)], name="log_entity_id_asc")
    logs.create_index([("action", ASCENDING)], name="log_action_asc")
