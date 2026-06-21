from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


def paginated(items: list[dict], total: int, page: int, limit: int) -> dict:
    return {"items": items, "total": total, "page": page, "limit": limit}

