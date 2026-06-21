from datetime import datetime, timezone
from typing import Optional
import uuid


class CertificateModel:
    collection_name = "certificates"

    @staticmethod
    def generate_id() -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short = uuid.uuid4().hex[:6].upper()
        return f"CERT-{date_str}-{short}"

    @staticmethod
    def new(
        application_id: str,
        parcel_code: str,
        owner_name: str,
        certificate_type: str,
        valid_until: Optional[datetime] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "certificate_id": CertificateModel.generate_id(),
            "application_id": application_id,
            "parcel_code": parcel_code,
            "owner_name": owner_name,
            "certificate_type": certificate_type,
            "issued_at": now,
            "valid_until": valid_until,
            "status": "active",
        }

    @staticmethod
    def serialize(doc: dict) -> dict:
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
