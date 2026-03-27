import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ──────────────────────────────────────────────
# Password utilities
# ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ──────────────────────────────────────────────
# Client secret / token utilities
# ──────────────────────────────────────────────

def hash_secret(secret: str) -> str:
    """Hash a client secret or token using SHA-256 (non-reversible)."""
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_secret(plain: str, hashed: str) -> bool:
    return secrets.compare_digest(
        hashlib.sha256(plain.encode()).hexdigest(), hashed
    )


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


# ──────────────────────────────────────────────
# JWT utilities
# ──────────────────────────────────────────────

def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iss": settings.ISSUER,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_aud": False},
    )


# ──────────────────────────────────────────────
# PKCE utilities
# ──────────────────────────────────────────────

def verify_pkce(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return secrets.compare_digest(computed, code_challenge)
    if method == "plain":
        return secrets.compare_digest(code_verifier, code_challenge)
    return False


# ──────────────────────────────────────────────
# Webhook HMAC signature
# ──────────────────────────────────────────────

def sign_webhook_payload(payload_bytes: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"
