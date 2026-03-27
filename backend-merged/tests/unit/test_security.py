"""
Unit tests for security utilities.
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.core.security import (
    hash_password,
    verify_password,
    hash_secret,
    verify_secret,
    generate_secure_token,
    create_access_token,
    decode_token,
    verify_pkce,
    sign_webhook_payload,
)


class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "my_secure_password"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "my_secure_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "my_secure_password"
        hashed = hash_password(password)
        
        assert verify_password("wrong_password", hashed) is False


class TestSecretHashing:
    """Test secret hashing functions."""
    
    def test_hash_secret(self):
        """Test secret hashing."""
        secret = "my_secret_key"
        hashed = hash_secret(secret)
        
        assert hashed != secret
        assert len(hashed) == 64  # SHA-256 hex digest
    
    def test_verify_secret_correct(self):
        """Test secret verification with correct secret."""
        secret = "my_secret_key"
        hashed = hash_secret(secret)
        
        assert verify_secret(secret, hashed) is True
    
    def test_verify_secret_incorrect(self):
        """Test secret verification with incorrect secret."""
        secret = "my_secret_key"
        hashed = hash_secret(secret)
        
        assert verify_secret("wrong_secret", hashed) is False


class TestTokenGeneration:
    """Test token generation."""
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = generate_secure_token(32)
        token2 = generate_secure_token(32)
        
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2
    
    def test_generate_secure_token_length(self):
        """Test token generation with different lengths."""
        token_16 = generate_secure_token(16)
        token_64 = generate_secure_token(64)
        
        assert len(token_16) < len(token_64)


class TestJWT:
    """Test JWT functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token(
            subject="user-123",
            extra_claims={"email": "test@example.com", "role": "user"},
        )
        
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 3 parts
    
    def test_decode_token(self):
        """Test token decoding."""
        subject = "user-123"
        extra_claims = {"email": "test@example.com", "role": "user"}
        
        token = create_access_token(subject=subject, extra_claims=extra_claims)
        decoded = decode_token(token)
        
        assert decoded["sub"] == subject
        assert decoded["email"] == extra_claims["email"]
        assert decoded["role"] == extra_claims["role"]
        assert "exp" in decoded
        assert "iat" in decoded
        assert "iss" in decoded
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        from jose import JWTError
        
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")


class TestPKCE:
    """Test PKCE functions."""
    
    def test_verify_pkce_s256_valid(self):
        """Test PKCE verification with S256 method."""
        import base64
        import hashlib
        
        code_verifier = "test_verifier_1234567890"
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        
        assert verify_pkce(code_verifier, code_challenge, "S256") is True
    
    def test_verify_pkce_s256_invalid(self):
        """Test PKCE verification with wrong verifier."""
        import base64
        import hashlib
        
        code_verifier = "test_verifier_1234567890"
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        
        assert verify_pkce("wrong_verifier", code_challenge, "S256") is False
    
    def test_verify_pkce_plain_valid(self):
        """Test PKCE verification with plain method."""
        code_verifier = "test_verifier"
        code_challenge = code_verifier
        
        assert verify_pkce(code_verifier, code_challenge, "plain") is True
    
    def test_verify_pkce_plain_invalid(self):
        """Test PKCE verification with plain method and wrong verifier."""
        code_challenge = "test_verifier"
        
        assert verify_pkce("wrong_verifier", code_challenge, "plain") is False


class TestWebhookSigning:
    """Test webhook payload signing."""
    
    def test_sign_webhook_payload(self):
        """Test webhook payload signing."""
        payload = b'{"event": "user.created", "user_id": "123"}'
        secret = "webhook_secret_key"
        
        signature = sign_webhook_payload(payload, secret)
        
        assert signature.startswith("sha256=")
        assert len(signature) > 7
    
    def test_sign_webhook_payload_deterministic(self):
        """Test that signing is deterministic."""
        payload = b'{"event": "test"}'
        secret = "secret"
        
        sig1 = sign_webhook_payload(payload, secret)
        sig2 = sign_webhook_payload(payload, secret)
        
        assert sig1 == sig2
    
    def test_sign_webhook_payload_different_secrets(self):
        """Test that different secrets produce different signatures."""
        payload = b'{"event": "test"}'
        
        sig1 = sign_webhook_payload(payload, "secret1")
        sig2 = sign_webhook_payload(payload, "secret2")
        
        assert sig1 != sig2
