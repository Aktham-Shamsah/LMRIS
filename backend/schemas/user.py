from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(default="", max_length=30)
    role: Literal["admin", "user"] = "user"


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=30)
    role: Optional[Literal["admin", "user"]] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[UserResponse]
