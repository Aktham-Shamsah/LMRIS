from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None
    errors: list[Any] = []


def ok(data: Any = None, message: str = "OK") -> dict:
    return {"success": True, "message": message, "data": data, "errors": []}

