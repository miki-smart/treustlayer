"""
Unit tests for security utilities: PKCE, hashing, JWT round-trip.
"""
import base64
import hashlib
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import security


# ── RSA key fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rsa_key_pair():
    """Generate a throwaway 2048-bit RSA key pair for test JWT operations."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


# ── PKCE ─────────────────────────────────────────────────────────────────────

class TestVerifyPKCE:
    def _make_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def test_s256_valid(self):
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = self._make_challenge(verifier)
        assert security.verify_pkce(verifier, challenge, method="S256") is True

    def test_s256_invalid_verifier(self):
        verifier = "correct-verifier"
        wrong_verifier = "wrong-verifier"
        challenge = self._make_challenge(verifier)
        assert security.verify_pkce(wrong_verifier, challenge, method="S256") is False

    def test_plain_valid(self):
        verifier = "my-plain-code-verifier"
        assert security.verify_pkce(verifier, verifier, method="plain") is True

    def test_plain_invalid(self):
        assert security.verify_pkce("verifier1", "verifier2", method="plain") is False

    def test_unknown_method_returns_false(self):
        assert security.verify_pkce("v", "c", method="md5") is False


# ── Secret hashing ────────────────────────────────────────────────────────────

class TestHashSecret:
    def test_hash_is_deterministic(self):
        assert security.hash_secret("hello") == security.hash_secret("hello")

    def test_different_inputs_differ(self):
        assert security.hash_secret("abc") != security.hash_secret("xyz")

    def test_verify_correct_secret(self):
        raw = "super-secret-value"
        hashed = security.hash_secret(raw)
        assert security.verify_secret(raw, hashed) is True

    def test_verify_wrong_secret(self):
        hashed = security.hash_secret("real")
        assert security.verify_secret("fake", hashed) is False


# ── Password hashing ──────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_round_trip(self):
        pw = "Str0ngP@ssword!"
        hashed = security.hash_password(pw)
        assert security.verify_password(pw, hashed) is True

    def test_wrong_password_rejected(self):
        hashed = security.hash_password("correct")
        assert security.verify_password("wrong", hashed) is False

    def test_unique_hashes(self):
        pw = "same-password"
        assert security.hash_password(pw) != security.hash_password(pw)  # bcrypt salts


# ── JWT ───────────────────────────────────────────────────────────────────────

class TestJWT:
    def test_create_and_decode(self, rsa_key_pair, monkeypatch):
        private_pem, public_pem = rsa_key_pair
        monkeypatch.setattr(security.settings, "JWT_PRIVATE_KEY", private_pem)
        monkeypatch.setattr(security.settings, "JWT_PUBLIC_KEY", public_pem)
        monkeypatch.setattr(security.settings, "JWT_ALGORITHM", "RS256")
        monkeypatch.setattr(security.settings, "ISSUER", "test-issuer")

        token = security.create_access_token(
            subject="user-abc",
            extra_claims={"scope": "openid profile.basic"},
            expires_delta=__import__("datetime").timedelta(minutes=5),
        )
        payload = security.decode_token(token)

        assert payload["sub"] == "user-abc"
        assert payload["iss"] == "test-issuer"
        assert "jti" in payload
        assert payload["scope"] == "openid profile.basic"

    def test_expired_token_raises(self, rsa_key_pair, monkeypatch):
        from datetime import timedelta
        from jose import ExpiredSignatureError

        private_pem, public_pem = rsa_key_pair
        monkeypatch.setattr(security.settings, "JWT_PRIVATE_KEY", private_pem)
        monkeypatch.setattr(security.settings, "JWT_PUBLIC_KEY", public_pem)
        monkeypatch.setattr(security.settings, "JWT_ALGORITHM", "RS256")
        monkeypatch.setattr(security.settings, "ISSUER", "test-issuer")

        token = security.create_access_token(
            subject="user-abc",
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        with pytest.raises(Exception):  # jose raises JWTError subclass
            security.decode_token(token)
