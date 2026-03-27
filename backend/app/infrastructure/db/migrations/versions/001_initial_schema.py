"""
Initial schema migration — creates all PostgreSQL schemas and tables.

Revision ID: 001
Revises: -
Create Date: 2026-03-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create schemas ────────────────────────────────────────────────────────
    for schema in [
        "identity",
        "kyc",
        "consent",
        "auth",
        "app_registry",
        "session",
        "event_store",
        "webhook",
    ]:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    # ── identity.users ────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="identity",
    )
    op.create_index("ix_identity_users_email", "users", ["email"], schema="identity")
    op.create_index("ix_identity_users_username", "users", ["username"], schema="identity")

    # ── app_registry.apps ─────────────────────────────────────────────────────
    op.create_table(
        "apps",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("client_id", sa.String(120), nullable=False, unique=True),
        sa.Column("client_secret_hash", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("allowed_scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("redirect_uris", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="app_registry",
    )
    op.create_index("ix_app_registry_apps_client_id", "apps", ["client_id"], schema="app_registry")

    # ── auth.authorization_codes ──────────────────────────────────────────────
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

    # ── kyc.verifications ─────────────────────────────────────────────────────
    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("tier", sa.String(20), nullable=False, server_default="tier_0"),
        sa.Column("trust_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("document_type", sa.String(100), nullable=True),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("document_url", sa.String(512), nullable=True),
        sa.Column("face_similarity_score", sa.Float, nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="kyc",
    )
    op.create_index("ix_kyc_verifications_user_id", "verifications", ["user_id"], schema="kyc")

    # ── consent.consents ──────────────────────────────────────────────────────
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

    # ── session.refresh_tokens ───────────────────────────────────────────────
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

    # ── webhook.subscriptions ────────────────────────────────────────────────
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

    # ── webhook.deliveries ───────────────────────────────────────────────────
    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("target_url", sa.String(512), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_code", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="webhook",
    )


def downgrade() -> None:
    op.drop_table("deliveries", schema="webhook")
    op.drop_table("subscriptions", schema="webhook")
    op.drop_table("refresh_tokens", schema="session")
    op.drop_table("consents", schema="consent")
    op.drop_table("verifications", schema="kyc")
    op.drop_table("authorization_codes", schema="auth")
    op.drop_table("apps", schema="app_registry")
    op.drop_table("users", schema="identity")

    for schema in ["identity", "kyc", "consent", "auth", "app_registry", "session", "event_store", "webhook"]:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
