"""TrustLayer ID API harmonization — new columns and tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-27 00:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_safe(name: str, *values: str) -> None:
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)}); "
        f"EXCEPTION WHEN duplicate_object THEN null; END $$;"
    ))


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    return conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).fetchone() is not None


def _table_exists(name: str) -> bool:
    return op.get_bind().dialect.has_table(op.get_bind(), name)


def upgrade() -> None:
    # ── New UserRole values ──────────────────────────────────────────────────
    for new_val in ("kyc_approver", "app_owner"):
        has = op.get_bind().execute(sa.text(
            "SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid=t.oid "
            "WHERE t.typname='userrole' AND e.enumlabel=:v"
        ), {"v": new_val}).fetchone()
        if not has:
            op.execute(sa.text(f"ALTER TYPE userrole ADD VALUE '{new_val}'"))

    # ── users: new columns ───────────────────────────────────────────────────
    if not _column_exists("users", "username"):
        op.add_column("users", sa.Column("username", sa.String(100), nullable=True))
        op.create_index("ix_users_username", "users", ["username"], unique=True)
    for col in [("refresh_tokens", "client_id", sa.String(100)), ("refresh_tokens", "scopes", sa.Text())]:
        if not _column_exists(col[0], col[1]):
            op.add_column(col[0], sa.Column(col[1], col[2], nullable=True))

    # ── kyc_applications: new columns ────────────────────────────────────────
    kyc_cols = [
        ("document_type", sa.String(100)),
        ("document_number", sa.String(100)),
        ("document_url", sa.String(500)),
        ("face_image_url", sa.String(500)),
        ("tier", sa.String(20)),
        ("face_similarity_score", sa.Float()),
        ("rejection_reason", sa.Text()),
    ]
    for col_name, col_type in kyc_cols:
        if not _column_exists("kyc_applications", col_name):
            nullable = col_name != "tier"
            default = "tier_0" if col_name == "tier" else None
            col = sa.Column(col_name, col_type, nullable=True)
            op.add_column("kyc_applications", col)
            if col_name == "tier":
                op.execute(sa.text("UPDATE kyc_applications SET tier = 'tier_0' WHERE tier IS NULL"))
                op.alter_column("kyc_applications", "tier", nullable=False, server_default="tier_0")

    # ── registered_apps: api_key ─────────────────────────────────────────────
    if not _column_exists("registered_apps", "api_key_hash"):
        op.add_column("registered_apps", sa.Column("api_key_hash", sa.String(255), nullable=True))

    # ── consent_grants ───────────────────────────────────────────────────────
    if not _table_exists("consent_grants"):
        op.create_table(
            "consent_grants",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("client_id", sa.String(100), nullable=False),
            sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_consent_grants_user_id", "consent_grants", ["user_id"])
        op.create_index("ix_consent_grants_client_id", "consent_grants", ["client_id"])

    # ── password_reset_tokens ────────────────────────────────────────────────
    if not _table_exists("password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token", sa.String(255), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_password_reset_tokens_token", "password_reset_tokens", ["token"])

    # ── email_verification_tokens ─────────────────────────────────────────────
    if not _table_exists("email_verification_tokens"):
        op.create_table(
            "email_verification_tokens",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token", sa.String(255), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_email_verification_tokens_token", "email_verification_tokens", ["token"])

    # ── webhook_subscriptions ─────────────────────────────────────────────────
    if not _table_exists("webhook_subscriptions"):
        op.create_table(
            "webhook_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("client_id", sa.String(100), nullable=False),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("target_url", sa.String(500), nullable=False),
            sa.Column("signing_secret", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_webhook_subscriptions_client_id", "webhook_subscriptions", ["client_id"])

    # ── webhook_deliveries_new ────────────────────────────────────────────────
    if not _table_exists("webhook_deliveries_new"):
        op.create_table(
            "webhook_deliveries_new",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("client_id", sa.String(100), nullable=False),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("target_url", sa.String(500), nullable=False),
            sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("response_code", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_webhook_deliveries_new_subscription_id", "webhook_deliveries_new", ["subscription_id"])


def downgrade() -> None:
    for tbl in ["webhook_deliveries_new", "webhook_subscriptions",
                "email_verification_tokens", "password_reset_tokens", "consent_grants"]:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
    for col in [("registered_apps", "api_key_hash"),
                ("refresh_tokens", "scopes"), ("refresh_tokens", "client_id"),
                ("users", "username")]:
        op.execute(sa.text(f"ALTER TABLE {col[0]} DROP COLUMN IF EXISTS {col[1]}"))
    for col in ["rejection_reason", "face_similarity_score", "tier", "face_image_url",
                "document_url", "document_number", "document_type"]:
        op.execute(sa.text(f"ALTER TABLE kyc_applications DROP COLUMN IF EXISTS {col}"))
