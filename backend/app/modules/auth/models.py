from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class CurrentUser(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    role: str
    actor_id: str | None = None
    active: bool = True

