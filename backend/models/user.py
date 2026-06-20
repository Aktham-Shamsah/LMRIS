from datetime import datetime, timezone


class UserModel:
    collection_name = "users"

    @staticmethod
    def new(name: str, email: str, phone: str = "", role: str = "user") -> dict:
        now = datetime.now(timezone.utc)
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "role": role,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def serialize(doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id", ""))
        return doc
