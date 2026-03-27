"""app marketplace, trust profiles, webhooks, user profile fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-27 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_safe(name: str, *values: str) -> None:
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)}); "
        f"EXCEPTION WHEN duplicate_object THEN null; END $$;"
    ))


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column}).fetchone()
    return result is not None


def upgrade() -> None:
    # --- New enums ---
    _create_enum_safe("appstatus", "pending", "approved", "rejected", "suspended")
    _create_enum_safe("appcategory", "banking", "lending", "payments", "insurance", "investment", "wallet", "other")

    # --- Add columns to existing users table ---
    if not _column_exists("users", "phone"):
        op.add_column("users", sa.Column("phone", sa.String(30), nullable=True, unique=True))
    if not _column_exists("users", "email_verified"):
        op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"))
    if not _column_exists("users", "phone_verified"):
        op.add_column("users", sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"))

    # --- Registered apps ---
    if not _table_exists("registered_apps"):
        op.create_table(
            "registered_apps",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("client_id", sa.String(100), nullable=False, unique=True),
            sa.Column("client_secret_hash", sa.String(255), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("logo_url", sa.String(500), nullable=True),
            sa.Column("website_url", sa.String(500), nullable=True),
            sa.Column("category", postgresql.ENUM("banking", "lending", "payments", "insurance", "investment", "wallet", "other", name="appcategory", create_type=False), nullable=False, server_default="other"),
            sa.Column("status", postgresql.ENUM("pending", "approved", "rejected", "suspended", name="appstatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("allowed_scopes", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("redirect_uris", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        )
        op.create_index("ix_registered_apps_client_id", "registered_apps", ["client_id"])
        op.create_index("ix_registered_apps_owner_id", "registered_apps", ["owner_id"])

    # --- Authorization codes (PKCE/OIDC) ---
    if not _table_exists("authorization_codes"):
        op.create_table(
            "authorization_codes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("code", sa.String(255), nullable=False, unique=True),
            sa.Column("app_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("registered_apps.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("redirect_uri", sa.String(500), nullable=False),
            sa.Column("code_challenge", sa.String(255), nullable=True),
            sa.Column("code_challenge_method", sa.String(10), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_authorization_codes_code", "authorization_codes", ["code"])

    # --- User ↔ App connections ---
    if not _table_exists("user_apps"):
        op.create_table(
            "user_apps",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("app_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("registered_apps.id", ondelete="CASCADE"), nullable=False),
            sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        )
        op.create_index("ix_user_apps_user_id", "user_apps", ["user_id"])

    # --- Trust profiles ---
    if not _table_exists("trust_profiles"):
        op.create_table(
            "trust_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("kyc_tier", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("factors", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("last_evaluated", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_trust_profiles_user_id", "trust_profiles", ["user_id"])

    # --- Webhook endpoints ---
    if not _table_exists("webhook_endpoints"):
        op.create_table(
            "webhook_endpoints",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("app_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("registered_apps.id", ondelete="CASCADE"), nullable=False),
            sa.Column("url", sa.String(500), nullable=False),
            sa.Column("events", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("secret", sa.String(255), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_webhook_endpoints_app_id", "webhook_endpoints", ["app_id"])

    # --- Webhook deliveries ---
    if not _table_exists("webhook_deliveries"):
        op.create_table(
            "webhook_deliveries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("response_status", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_webhook_deliveries_endpoint_id", "webhook_deliveries", ["endpoint_id"])


def downgrade() -> None:
    for tbl in [
        "webhook_deliveries", "webhook_endpoints", "trust_profiles",
        "user_apps", "authorization_codes", "registered_apps",
    ]:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))

    for col in [("users", "phone_verified"), ("users", "email_verified"), ("users", "phone")]:
        op.execute(sa.text(f"ALTER TABLE {col[0]} DROP COLUMN IF EXISTS {col[1]}"))

    for name in ["appcategory", "appstatus"]:
        op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))
