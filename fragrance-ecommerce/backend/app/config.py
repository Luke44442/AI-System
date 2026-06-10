from __future__ import annotations
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    APP_NAME: str = "Aurevia API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development|staging|production
    SECRET_KEY: str = Field(default="change-me-in-production-minimum-32-chars!!")
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> List[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v  # type: ignore[return-value]

    DATABASE_URL: str = "postgresql+asyncpg://aurevia_user:aurevia_pass@localhost:5432/aurevia"
    DATABASE_POOL_SIZE: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    JWT_SECRET_KEY: str = Field(default="change-me-jwt-secret-minimum-32-chars!!")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: Optional[str] = "aurevia-media"
    R2_PUBLIC_URL: Optional[str] = None

    ANTHROPIC_API_KEY: Optional[str] = None
    AI_MODEL: str = "claude-opus-4-8"

    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    ETSY_API_KEY: Optional[str] = None
    ETSY_ACCESS_TOKEN: Optional[str] = None
    ETSY_SHOP_ID: Optional[str] = None

    EBAY_APP_ID: Optional[str] = None
    EBAY_CERT_ID: Optional[str] = None
    EBAY_USER_TOKEN: Optional[str] = None
    EBAY_SANDBOX: bool = True

    TIKTOK_SHOP_APP_KEY: Optional[str] = None
    TIKTOK_SHOP_ACCESS_TOKEN: Optional[str] = None
    PINTEREST_ACCESS_TOKEN: Optional[str] = None
    GOOGLE_MERCHANT_ID: Optional[str] = None
    GOOGLE_MERCHANT_CREDENTIALS_JSON: Optional[str] = None

    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "hello@aurevia.com"

    SENTRY_DSN: Optional[str] = None

    ENABLE_AI_LISTINGS: bool = True
    ENABLE_AUTO_PRICING: bool = True
    ENABLE_MARKETPLACE_SYNC: bool = True

    _INSECURE_DEFAULTS = {
        "change-me-in-production-minimum-32-chars!!",
        "change-me-jwt-secret-minimum-32-chars!!",
    }

    @field_validator("SECRET_KEY", "JWT_SECRET_KEY")
    @classmethod
    def _no_insecure_secret_in_prod(cls, v: str, info) -> str:
        # Block the shipped placeholder secrets when running in production.
        import os
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production" and v in cls._INSECURE_DEFAULTS:
            raise ValueError(
                f"{info.field_name} must be overridden in production — "
                "the default placeholder secret is not allowed."
            )
        return v


settings = Settings()
