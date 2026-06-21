import re
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def next_yearly_id(db, collection_name: str, field: str, prefix: str) -> str:
    year = utc_now().year
    pattern = f"^{prefix}-{year}-"
    latest = db[collection_name].find_one({field: {"$regex": pattern}}, sort=[(field, -1)])
    if latest and latest.get(field):
        match = re.search(r"(\d+)$", latest[field])
        number = int(match.group(1)) + 1 if match else 1
    else:
        number = 1
    return f"{prefix}-{year}-{number:04d}"

