from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit
