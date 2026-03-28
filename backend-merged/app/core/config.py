import logging
from functools import lru_cache
from typing import List

from cryptography.hazmat.primitives import serialization
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.dev_jwt_keys import DEV_JWT_PRIVATE_KEY, DEV_JWT_PUBLIC_KEY

logger = logging.getLogger(__name__)


def _normalize_jwt_pem(value: str) -> str:
    """Fix PEM from .env where newlines are escaped as \\n on one line."""
    if not value:
        return ""
    v = value.strip()
    if "\\n" in v:
        v = v.replace("\\n", "\n")
    return v


def _rsa_pem_pair_valid(private_pem: str, public_pem: str) -> bool:
    if not private_pem or not public_pem:
        return False
    try:
        serialization.load_pem_private_key(private_pem.encode(), password=None)
        serialization.load_pem_public_key(public_pem.encode())
        return True
    except Exception:
        return False


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
    # client_id on refresh tokens from POST /auth/login; SPA must use same client_id for /auth/token refresh grant.
    DIRECT_LOGIN_REFRESH_CLIENT_ID: str = "trustlayer-spa"

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
    # Skip Gemini entirely; return empty extract + success (manual entry in UI).
    GEMINI_OCR_MOCK: bool = False
    # On 429 / quota errors, return empty extract so the wizard still works (demo / dev).
    GEMINI_OCR_FALLBACK_MOCK_ON_QUOTA: bool = True

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

    @model_validator(mode="after")
    def _resolve_rs256_jwt_keys(self) -> "Settings":
        self.JWT_PRIVATE_KEY = _normalize_jwt_pem(self.JWT_PRIVATE_KEY)
        self.JWT_PUBLIC_KEY = _normalize_jwt_pem(self.JWT_PUBLIC_KEY)
        if self.JWT_ALGORITHM != "RS256":
            return self
        if _rsa_pem_pair_valid(self.JWT_PRIVATE_KEY, self.JWT_PUBLIC_KEY):
            return self
        if self.APP_ENV == "development":
            any_provided = bool(
                self.JWT_PRIVATE_KEY.strip() or self.JWT_PUBLIC_KEY.strip()
            )
            if any_provided:
                logger.warning(
                    "JWT_PRIVATE_KEY/JWT_PUBLIC_KEY are set but not valid RSA PEMs; "
                    "using built-in dev keys. Fix or clear them (see scripts/generate_keys.py)."
                )
            else:
                logger.debug(
                    "JWT keys unset; using built-in dev RSA keys for development."
                )
            self.JWT_PRIVATE_KEY = DEV_JWT_PRIVATE_KEY
            self.JWT_PUBLIC_KEY = DEV_JWT_PUBLIC_KEY
            return self
        raise ValueError(
            "RS256 requires valid JWT_PRIVATE_KEY and JWT_PUBLIC_KEY (PEM). "
            "Run: python scripts/generate_keys.py"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
