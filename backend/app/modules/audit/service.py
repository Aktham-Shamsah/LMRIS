from app.modules.audit.repository import AuditRepository
from app.shared.ids import utc_now


class AuditService:
    def __init__(self, repo: AuditRepository | None = None) -> None:
        self.repo = repo or AuditRepository()

    def record(
        self,
        application_id: str,
        event_type: str,
        actor_type: str = "system",
        actor_id: str = "system",
        meta: dict | None = None,
    ) -> dict:
        event = {
            "type": event_type,
            "by": {"actor_type": actor_type, "actor_id": actor_id},
            "at": utc_now(),
            "meta": meta or {},
        }
        return self.repo.append_event(application_id, event)

    def timeline(self, application_id: str) -> list[dict]:
        return self.repo.get_timeline(application_id)

