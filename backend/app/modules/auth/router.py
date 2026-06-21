from fastapi import APIRouter, Depends

from app.modules.auth.models import CurrentUser, LoginRequest, TokenResponse
from app.modules.auth.service import authenticate, create_access_token, public_user
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate(str(payload.email), payload.password)
    return TokenResponse(access_token=create_access_token(user), user=public_user(user))


@router.get("/me", response_model=CurrentUser)
def me(user: CurrentUser = Depends(get_current_user)):
    return user

