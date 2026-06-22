from fastapi import APIRouter, Depends

from app.modules.auth.models import CurrentUser, LoginRequest, ResendOtpRequest, SignupRequest, TokenResponse, VerifyEmailRequest
from app.modules.auth.service import authenticate, create_access_token, public_user, send_signup_otp, signup, verify_signup_otp
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate(str(payload.email), payload.password)
    return TokenResponse(access_token=create_access_token(user), user=public_user(user))


@router.post("/signup", status_code=201)
def create_signup(payload: SignupRequest):
    return signup(payload)


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(payload: VerifyEmailRequest):
    user = verify_signup_otp(str(payload.email), payload.otp_code)
    return TokenResponse(access_token=create_access_token(user), user=public_user(user))


@router.post("/resend-otp")
def resend_otp(payload: ResendOtpRequest):
    return send_signup_otp(str(payload.email))


@router.get("/me", response_model=CurrentUser)
def me(user: CurrentUser = Depends(get_current_user)):
    return user

