from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LRMIS"
    api_prefix: str = ""
    environment: str = "development"
    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db: str = Field(default="lrmis", alias="MONGODB_DB")
    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173", alias="CORS_ORIGINS")
    simple_staff_token: str = Field(default="dev-staff-token", alias="SIMPLE_STAFF_TOKEN")
    jwt_secret_key: str = Field(default="lrmis-demo-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_minutes: int = Field(default=240, alias="JWT_ACCESS_TOKEN_MINUTES")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_unauthenticated_per_minute: int = Field(default=30, alias="RATE_LIMIT_UNAUTHENTICATED_PER_MINUTE")
    rate_limit_login_per_minute: int = Field(default=5, alias="RATE_LIMIT_LOGIN_PER_MINUTE")
    rate_limit_applicant_per_minute: int = Field(default=120, alias="RATE_LIMIT_APPLICANT_PER_MINUTE")
    rate_limit_surveyor_per_minute: int = Field(default=180, alias="RATE_LIMIT_SURVEYOR_PER_MINUTE")
    rate_limit_registrar_per_minute: int = Field(default=240, alias="RATE_LIMIT_REGISTRAR_PER_MINUTE")
    rate_limit_supervisor_per_minute: int = Field(default=300, alias="RATE_LIMIT_SUPERVISOR_PER_MINUTE")
    rate_limit_admin_per_minute: int = Field(default=300, alias="RATE_LIMIT_ADMIN_PER_MINUTE")
    email_enabled: bool = Field(default=False, alias="EMAIL_ENABLED")
    email_send_immediately: bool = Field(default=True, alias="EMAIL_SEND_IMMEDIATELY")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    mail_from: str | None = Field(default=None, alias="MAIL_FROM")
    mail_from_name: str = Field(default="LRMIS", alias="MAIL_FROM_NAME")
    reply_to: str | None = Field(default=None, alias="REPLY_TO")
    email_redirect_to: str | None = Field(default=None, alias="EMAIL_REDIRECT_TO")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    email_otp_minutes: int = Field(default=10, alias="EMAIL_OTP_MINUTES")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

