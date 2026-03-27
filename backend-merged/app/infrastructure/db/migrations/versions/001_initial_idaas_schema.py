"""
Initial IDaaS schema migration.

Creates 11 PostgreSQL schemas with schema isolation:
- identity: User management
- auth: OIDC/OAuth2 authorization codes
- kyc: KYC verification (enhanced)
- trust: Trust scoring (enhanced)
- biometric: Face + voice verification (NEW)
- digital_identity: DID system (NEW)
- consent: Consent management
- app_registry: OAuth2 clients
- session: Refresh tokens
- webhook: Event delivery
- audit: Audit logging

Revision ID: 001_initial_idaas_schema
Revises: -
Create Date: 2026-03-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_idaas_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for schema in [
        "identity",
        "auth",
        "kyc",
        "trust",
        "biometric",
        "digital_identity",
        "consent",
        "app_registry",
        "session",
        "webhook",
        "audit",
    ]:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("avatar", sa.String(500), nullable=True),
        sa.Column("role", sa.String(30), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("phone_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("email_verification_token_hash", sa.String(255), nullable=True),
        sa.Column("email_verification_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_reset_token_hash", sa.String(255), nullable=True),
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="identity",
    )
    op.create_index("ix_identity_users_email", "users", ["email"], schema="identity")
    op.create_index("ix_identity_users_username", "users", ["username"], schema="identity")

    op.create_table(
        "authorization_codes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("redirect_uri", sa.String(512), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("code_challenge", sa.String(256), nullable=True),
        sa.Column("code_challenge_method", sa.String(10), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="auth",
    )
    op.create_index("ix_auth_authorization_codes_code", "authorization_codes", ["code"], schema="auth")

    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("tier", sa.String(20), nullable=False, server_default="tier_0"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("place_of_birth", sa.String(255), nullable=True),
        sa.Column("document_type", sa.String(100), nullable=True),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("issue_date", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("billing_name", sa.String(255), nullable=True),
        sa.Column("service_provider", sa.String(255), nullable=True),
        sa.Column("service_type", sa.String(100), nullable=True),
        sa.Column("bill_date", sa.Date, nullable=True),
        sa.Column("account_number", sa.String(100), nullable=True),
        sa.Column("mrz_line1", sa.String(255), nullable=True),
        sa.Column("mrz_line2", sa.String(255), nullable=True),
        sa.Column("id_front_url", sa.String(512), nullable=True),
        sa.Column("id_back_url", sa.String(512), nullable=True),
        sa.Column("utility_bill_url", sa.String(512), nullable=True),
        sa.Column("face_image_url", sa.String(512), nullable=True),
        sa.Column("documents_submitted", postgresql.JSONB, nullable=True, server_default="[]"),
        sa.Column("extracted_data", postgresql.JSONB, nullable=True),
        sa.Column("id_ocr_confidence", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("utility_ocr_confidence", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("overall_confidence", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("synthetic_id_probability", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("face_similarity_score", sa.Float, nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="kyc",
    )
    op.create_index("ix_kyc_verifications_user_id", "verifications", ["user_id"], schema="kyc")
    op.create_index("ix_kyc_verifications_status", "verifications", ["status"], schema="kyc")
    op.create_index("ix_kyc_verifications_tier", "verifications", ["tier"], schema="kyc")

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column("trust_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("kyc_tier", sa.Integer, nullable=False, server_default="0"),
        sa.Column("face_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("voice_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("digital_identity_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("factors", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("last_evaluated", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="trust",
    )
    op.create_index("ix_trust_profiles_user_id", "profiles", ["user_id"], schema="trust")

    op.create_table(
        "records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("liveness_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("spoof_probability", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("quality_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("device_info", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(100), nullable=True),
        sa.Column("biometric_data_url", sa.String(512), nullable=True),
        sa.Column("biometric_hash", sa.String(255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="biometric",
    )
    op.create_index("ix_biometric_records_user_id", "records", ["user_id"], schema="biometric")
    op.create_index("ix_biometric_records_type", "records", ["type"], schema="biometric")
    op.create_index("ix_biometric_records_status", "records", ["status"], schema="biometric")

    op.create_table(
        "identities",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column("unique_id", sa.String(500), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="digital_identity",
    )
    op.create_index("ix_digital_identities_user_id", "identities", ["user_id"], schema="digital_identity")
    op.create_index("ix_digital_identities_unique_id", "identities", ["unique_id"], schema="digital_identity")

    op.create_table(
        "attributes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("identity_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("is_shared", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="digital_identity",
    )
    op.create_index("ix_identity_attributes_identity_id", "attributes", ["identity_id"], schema="digital_identity")

    op.create_table(
        "credentials",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("identity_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("type", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(255), nullable=False),
        sa.Column("credential_data", postgresql.JSONB, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="digital_identity",
    )
    op.create_index("ix_identity_credentials_identity_id", "credentials", ["identity_id"], schema="digital_identity")

    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        schema="consent",
    )
    op.create_index("ix_consent_consents_user_id", "consents", ["user_id"], schema="consent")
    op.create_index("ix_consent_consents_client_id", "consents", ["client_id"], schema="consent")

    op.create_table(
        "apps",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("client_id", sa.String(120), nullable=False, unique=True),
        sa.Column("client_secret_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="other"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("allowed_scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("redirect_uris", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("owner_id", sa.String(255), nullable=True),
        sa.Column("api_key_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="app_registry",
    )
    op.create_index("ix_app_registry_apps_client_id", "apps", ["client_id"], schema="app_registry")
    op.create_index("ix_app_registry_apps_category", "apps", ["category"], schema="app_registry")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("is_revoked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="session",
    )
    op.create_index("ix_session_refresh_tokens_hash", "refresh_tokens", ["token_hash"], schema="session")
    op.create_index("ix_session_refresh_tokens_user_id", "refresh_tokens", ["user_id"], schema="session")

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("target_url", sa.String(512), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="webhook",
    )
    op.create_index("ix_webhook_subscriptions_client_id", "subscriptions", ["client_id"], schema="webhook")

    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("target_url", sa.String(512), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="5"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_code", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="webhook",
    )
    op.create_index("ix_webhook_deliveries_status", "deliveries", ["status"], schema="webhook")

    op.create_table(
        "entries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(100), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="audit",
    )
    op.create_index("ix_audit_entries_actor_id", "entries", ["actor_id"], schema="audit")
    op.create_index("ix_audit_entries_resource_type", "entries", ["resource_type"], schema="audit")
    op.create_index("ix_audit_entries_timestamp", "entries", ["timestamp"], schema="audit")


def downgrade() -> None:
    for schema in [
        "audit",
        "webhook",
        "session",
        "app_registry",
        "consent",
        "digital_identity",
        "biometric",
        "trust",
        "kyc",
        "auth",
        "identity",
    ]:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
