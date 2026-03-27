from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Merged configuration from Backend #1 and Backend #2.
    
    Security: RSA-256 JWT (from Backend #1)
    AI: Gemini OCR (from Backend #2)
    Features: IDaaS + Federated SSO
    """
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "TrustLayer ID"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trustlayer"

    # JWT / Security (RSA from Backend #1)
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OIDC
    ISSUER: str = "http://localhost:8000"
    AUTHORIZATION_ENDPOINT: str = "http://localhost:8000/api/v1/auth/authorize"
    TOKEN_ENDPOINT: str = "http://localhost:8000/api/v1/auth/token"
    USERINFO_ENDPOINT: str = "http://localhost:8000/api/v1/auth/userinfo"
    JWKS_URI: str = "http://localhost:8000/oauth/.well-known/jwks.json"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # Gemini AI (OCR from Backend #2)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Webhook
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_RETRY_DELAY_SECONDS: int = 60
    WEBHOOK_MAX_DELAY_SECONDS: int = 3600

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Email (placeholder for future SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@trustlayer.id"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
