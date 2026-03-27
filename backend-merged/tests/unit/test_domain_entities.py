"""
Unit tests for domain entities.
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.consent.domain.entities.consent_record import ConsentRecord
from app.modules.app_registry.domain.entities.app import App
from app.modules.kyc.domain.entities.kyc_verification import (
    KYCVerification,
    KYCStatus,
    KYCTier,
)
from app.modules.webhook.domain.entities.webhook_subscription import WebhookSubscription
from app.modules.webhook.domain.entities.webhook_delivery import (
    WebhookDelivery,
    DeliveryStatus,
)
from app.modules.audit.domain.entities.audit_entry import AuditEntry


class TestRefreshToken:
    """Test RefreshToken entity."""
    
    def test_refresh_token_creation(self):
        """Test creating refresh token."""
        token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid", "profile"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        assert token.user_id == "user-123"
        assert token.client_id == "client-123"
        assert token.is_revoked is False
        assert len(token.id) > 0
    
    def test_refresh_token_is_expired(self):
        """Test token expiration check."""
        expired_token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        
        valid_token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        assert expired_token.is_expired() is True
        assert valid_token.is_expired() is False
    
    def test_refresh_token_revoke(self):
        """Test token revocation."""
        token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        assert token.is_revoked is False
        token.revoke()
        assert token.is_revoked is True
    
    def test_refresh_token_is_valid(self):
        """Test token validity check."""
        valid_token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        
        expired_token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        
        revoked_token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=True,
        )
        
        assert valid_token.is_valid() is True
        assert expired_token.is_valid() is False
        assert revoked_token.is_valid() is False


class TestAuthorizationCode:
    """Test AuthorizationCode entity."""
    
    def test_authorization_code_creation(self):
        """Test creating authorization code."""
        code = AuthorizationCode(
            client_id="client-123",
            user_id="user-123",
            redirect_uri="http://localhost:3000/callback",
            scopes=["openid", "profile"],
        )
        
        assert len(code.code) > 0
        assert len(code.id) > 0
        assert code.is_used is False
    
    def test_authorization_code_requires_pkce(self):
        """Test PKCE requirement check."""
        code_without_pkce = AuthorizationCode(
            client_id="client-123",
            user_id="user-123",
            redirect_uri="http://localhost:3000",
            scopes=["openid"],
        )
        
        code_with_pkce = AuthorizationCode(
            client_id="client-123",
            user_id="user-123",
            redirect_uri="http://localhost:3000",
            scopes=["openid"],
            code_challenge="challenge",
            code_challenge_method="S256",
        )
        
        assert code_without_pkce.requires_pkce() is False
        assert code_with_pkce.requires_pkce() is True


class TestConsentRecord:
    """Test ConsentRecord entity."""
    
    def test_consent_creation(self):
        """Test creating consent record."""
        consent = ConsentRecord(
            user_id="user-123",
            client_id="client-123",
            scopes=["openid", "profile"],
        )
        
        assert consent.is_active is True
        assert consent.revoked_at is None
        assert len(consent.id) > 0
    
    def test_consent_revoke(self):
        """Test consent revocation."""
        consent = ConsentRecord(
            user_id="user-123",
            client_id="client-123",
            scopes=["openid"],
        )
        
        assert consent.is_active is True
        consent.revoke()
        assert consent.is_active is False
        assert consent.revoked_at is not None
    
    def test_consent_update_scopes(self):
        """Test updating consent scopes."""
        consent = ConsentRecord(
            user_id="user-123",
            client_id="client-123",
            scopes=["openid"],
        )
        
        consent.update_scopes(["openid", "profile", "email"])
        assert len(consent.scopes) == 3
        assert "email" in consent.scopes


class TestKYCVerification:
    """Test KYCVerification entity."""
    
    def test_kyc_creation(self):
        """Test creating KYC verification."""
        kyc = KYCVerification(
            user_id="user-123",
            status=KYCStatus.PENDING,
        )
        
        assert kyc.status == KYCStatus.PENDING
        assert kyc.tier == KYCTier.TIER_0
        assert len(kyc.id) > 0
    
    def test_kyc_submit(self):
        """Test KYC submission."""
        kyc = KYCVerification(user_id="user-123")
        
        kyc.submit()
        
        assert kyc.status == KYCStatus.PENDING
        assert kyc.submitted_at is not None
    
    def test_kyc_approve(self):
        """Test KYC approval."""
        kyc = KYCVerification(user_id="user-123", status=KYCStatus.PENDING)
        
        kyc.approve(reviewer_id="admin-123", tier=KYCTier.TIER_2)
        
        assert kyc.status == KYCStatus.APPROVED
        assert kyc.tier == KYCTier.TIER_2
        assert kyc.reviewer_id == "admin-123"
        assert kyc.reviewed_at is not None
        assert kyc.verified_at is not None
    
    def test_kyc_reject(self):
        """Test KYC rejection."""
        kyc = KYCVerification(user_id="user-123", status=KYCStatus.PENDING)
        
        kyc.reject(reviewer_id="admin-123", reason="Documents unclear")
        
        assert kyc.status == KYCStatus.REJECTED
        assert kyc.rejection_reason == "Documents unclear"
        assert kyc.reviewer_id == "admin-123"
        assert kyc.reviewed_at is not None


class TestApp:
    """Test App entity."""
    
    def test_app_creation(self):
        """Test creating app."""
        app = App(
            name="Test App",
            owner_id="user-123",
            allowed_scopes=["openid", "profile"],
            redirect_uris=["http://localhost:3000"],
        )
        
        assert app.name == "Test App"
        assert app.is_active is True
        assert app.is_approved is False
        assert len(app.client_id) > 0
    
    def test_app_approve(self):
        """Test app approval."""
        app = App(
            name="Test App",
            owner_id="user-123",
            allowed_scopes=["openid"],
            redirect_uris=["http://localhost:3000"],
            is_approved=False,
        )
        
        app.approve()
        
        assert app.is_approved is True
    
    def test_app_deactivate(self):
        """Test app deactivation."""
        app = App(
            name="Test App",
            owner_id="user-123",
            allowed_scopes=["openid"],
            redirect_uris=["http://localhost:3000"],
            is_active=True,
        )
        
        app.deactivate()
        
        assert app.is_active is False


class TestWebhookDelivery:
    """Test WebhookDelivery entity."""
    
    def test_webhook_delivery_creation(self):
        """Test creating webhook delivery."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={"user_id": "user-123"},
            target_url="https://example.com/webhook",
        )
        
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.attempts == 0
        assert len(delivery.id) > 0
    
    def test_webhook_delivery_mark_success(self):
        """Test marking delivery as successful."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={},
            target_url="https://example.com/webhook",
        )
        
        delivery.mark_success(response_status=200, response_body="OK")
        
        assert delivery.status == DeliveryStatus.SUCCESS
        assert delivery.response_status == 200
        assert delivery.attempts == 1
        assert delivery.last_attempt_at is not None
    
    def test_webhook_delivery_mark_failed_with_retry(self):
        """Test marking delivery as failed with retry."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={},
            target_url="https://example.com/webhook",
        )
        
        next_retry = datetime.now(timezone.utc) + timedelta(minutes=5)
        delivery.mark_failed(
            error_message="Connection timeout",
            response_status=None,
            next_retry_at=next_retry,
        )
        
        assert delivery.status == DeliveryStatus.RETRYING
        assert delivery.error_message == "Connection timeout"
        assert delivery.attempts == 1
        assert delivery.next_retry_at == next_retry
    
    def test_webhook_delivery_mark_failed_no_retry(self):
        """Test marking delivery as permanently failed."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={},
            target_url="https://example.com/webhook",
        )
        
        delivery.mark_failed(error_message="Max retries exceeded", next_retry_at=None)
        
        assert delivery.status == DeliveryStatus.FAILED
        assert delivery.next_retry_at is None


class TestAuditEntry:
    """Test AuditEntry entity."""
    
    def test_audit_entry_creation(self):
        """Test creating audit entry."""
        entry = AuditEntry(
            action="user.created",
            resource_type="user",
            actor_id="admin-123",
            resource_id="user-123",
            metadata={"ip_address": "127.0.0.1"},
        )
        
        assert entry.action == "user.created"
        assert entry.resource_type == "user"
        assert entry.actor_id == "admin-123"
        assert len(entry.id) > 0
        assert entry.timestamp is not None
    
    def test_audit_entry_system_action(self):
        """Test audit entry for system action."""
        entry = AuditEntry(
            action="system.cleanup",
            resource_type="session",
            actor_id=None,
            metadata={"deleted_count": 10},
        )
        
        assert entry.actor_id is None
        assert entry.metadata["deleted_count"] == 10
