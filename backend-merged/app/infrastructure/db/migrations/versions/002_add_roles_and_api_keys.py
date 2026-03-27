"""
Add enhanced tables for new features.

Adds:
- session.refresh_tokens: device_info, ip_address, last_used_at columns
- consent.consent_records: replaces old consents table
- app_registry.apps: updated schema
- webhook.webhook_subscriptions: replaces old subscriptions
- webhook.webhook_deliveries: replaces old deliveries
- audit.audit_entries: new audit logging table

Revision ID: 002_add_roles_and_api_keys
Revises: 001_initial_idaas_schema
Create Date: 2026-03-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision id must match alembic_version in DB (historical name; migration adds enhanced tables).
revision: str = "002_add_roles_and_api_keys"
down_revision: Union[str, None] = "001_initial_idaas_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update refresh_tokens table with new columns
    op.add_column(
        "refresh_tokens",
        sa.Column("device_info", sa.String(500), nullable=True),
        schema="session",
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("ip_address", sa.String(50), nullable=True),
        schema="session",
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        schema="session",
    )
    
    # Drop old consents table and create new consent_records
    op.drop_table("consents", schema="consent")
    
    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        schema="consent",
    )
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"], schema="consent")
    op.create_index("ix_consent_records_client_id", "consent_records", ["client_id"], schema="consent")
    
    # Drop old webhook tables and create new ones
    op.drop_table("deliveries", schema="webhook")
    op.drop_table("subscriptions", schema="webhook")
    
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("client_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("target_url", sa.String(512), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="webhook",
    )
    op.create_index("ix_webhook_subscriptions_client_id", "webhook_subscriptions", ["client_id"], schema="webhook")
    op.create_index("ix_webhook_subscriptions_event_type", "webhook_subscriptions", ["event_type"], schema="webhook")
    
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("target_url", sa.String(512), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status", sa.Integer, nullable=True),
        sa.Column("response_body", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="webhook",
    )
    op.create_index("ix_webhook_deliveries_subscription_id", "webhook_deliveries", ["subscription_id"], schema="webhook")
    op.create_index("ix_webhook_deliveries_status", "webhook_deliveries", ["status"], schema="webhook")
    op.create_index("ix_webhook_deliveries_next_retry_at", "webhook_deliveries", ["next_retry_at"], schema="webhook")
    
    # Create audit_entries table
    op.create_table(
        "audit_entries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("changes", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="audit",
    )
    op.create_index("ix_audit_entries_actor_id", "audit_entries", ["actor_id"], schema="audit")
    op.create_index("ix_audit_entries_action", "audit_entries", ["action"], schema="audit")
    op.create_index("ix_audit_entries_resource_type", "audit_entries", ["resource_type"], schema="audit")
    op.create_index("ix_audit_entries_resource_id", "audit_entries", ["resource_id"], schema="audit")
    op.create_index("ix_audit_entries_timestamp", "audit_entries", ["timestamp"], schema="audit")


def downgrade() -> None:
    # Drop new tables
    op.drop_table("audit_entries", schema="audit")
    op.drop_table("webhook_deliveries", schema="webhook")
    op.drop_table("webhook_subscriptions", schema="webhook")
    op.drop_table("consent_records", schema="consent")
    
    # Remove columns from refresh_tokens
    op.drop_column("refresh_tokens", "last_used_at", schema="session")
    op.drop_column("refresh_tokens", "ip_address", schema="session")
    op.drop_column("refresh_tokens", "device_info", schema="session")
    
    # Recreate old tables (simplified - in production, preserve data)
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
