from datetime import datetime, timezone


class ParcelModel:
    collection_name = "parcels"

    STATUSES = ["active", "inactive", "under_transfer", "subdivided"]

    @staticmethod
    def new(
        parcel_code: str,
        parcel_number: str,
        zone_id: str,
        owner: dict,
        area: float,
        geometry: dict,
        land_use: str = "",
        description: str = "",
        status: str = "active",
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "parcel_code": parcel_code,
            "parcel_number": parcel_number,
            "zone_id": zone_id,
            "owner": owner,
            "area": area,
            "geometry": geometry,
            "land_use": land_use,
            "description": description,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def serialize(doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
