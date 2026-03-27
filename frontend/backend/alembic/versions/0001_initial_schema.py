"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_safe(name: str, *values: str) -> None:
    """Create a PostgreSQL ENUM type only if it does not already exist."""
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)}); "
        f"EXCEPTION WHEN duplicate_object THEN null; END $$;"
    ))


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    # --- Enums (idempotent) ---
    _create_enum_safe("userrole", "admin", "user")
    _create_enum_safe("biometrictype", "face", "voice")
    _create_enum_safe("biometricstatus", "pending", "verified", "failed", "flagged")
    _create_enum_safe("risklevel", "low", "medium", "high")
    _create_enum_safe("kycstatus", "pending", "in_review", "approved", "rejected", "flagged")
    _create_enum_safe("identitystatus", "active", "suspended", "revoked", "pending")
    _create_enum_safe("ssoprotocol", "oauth2", "openid_connect", "saml")
    _create_enum_safe("ssoproviderstatus", "active", "inactive", "pending")
    _create_enum_safe("ssosessionstatus", "active", "expired", "revoked")
    _create_enum_safe("consentstatus", "active", "revoked")
    _create_enum_safe("cardstatus", "active", "frozen", "pending", "expired", "revoked")
    _create_enum_safe("cardtype", "virtual", "physical", "biometric")
    _create_enum_safe("transactiontype", "payment", "withdrawal", "transfer", "refund")
    _create_enum_safe("transactionstatus", "completed", "pending", "failed", "flagged")

    # --- Tables (skip if already exist) ---
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("role", postgresql.ENUM("admin", "user", name="userrole", create_type=False), nullable=False, server_default="user"),
            sa.Column("avatar", sa.String(500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_users_email", "users", ["email"])

    if not _table_exists("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token", sa.Text(), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"])

    if not _table_exists("biometric_records"):
        op.create_table(
            "biometric_records",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", postgresql.ENUM("face", "voice", name="biometrictype", create_type=False), nullable=False),
            sa.Column("status", postgresql.ENUM("pending", "verified", "failed", "flagged", name="biometricstatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("liveness_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("spoof_probability", sa.Float(), nullable=False, server_default="0"),
            sa.Column("risk_level", postgresql.ENUM("low", "medium", "high", name="risklevel", create_type=False), nullable=False, server_default="medium"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_biometric_records_user_id", "biometric_records", ["user_id"])

    if not _table_exists("kyc_applications"):
        op.create_table(
            "kyc_applications",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", postgresql.ENUM("pending", "in_review", "approved", "rejected", "flagged", name="kycstatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("documents_submitted", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("ocr_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("synthetic_id_probability", sa.Float(), nullable=False, server_default="0"),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("extracted_data", postgresql.JSONB(), nullable=True),
        )
        op.create_index("ix_kyc_applications_user_id", "kyc_applications", ["user_id"])

    if not _table_exists("digital_identities"):
        op.create_table(
            "digital_identities",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("unique_id", sa.String(500), nullable=False, unique=True),
            sa.Column("status", postgresql.ENUM("active", "suspended", "revoked", "pending", name="identitystatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("last_verified", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_digital_identities_user_id", "digital_identities", ["user_id"])

    if not _table_exists("identity_attributes"):
        op.create_table(
            "identity_attributes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("identity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("digital_identities.id", ondelete="CASCADE"), nullable=False),
            sa.Column("key", sa.String(255), nullable=False),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("shared", sa.Boolean(), nullable=False, server_default="false"),
        )
        op.create_index("ix_identity_attributes_identity_id", "identity_attributes", ["identity_id"])

    if not _table_exists("identity_credentials"):
        op.create_table(
            "identity_credentials",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("identity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("digital_identities.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.String(255), nullable=False),
            sa.Column("issuer", sa.String(255), nullable=False),
            sa.Column("expires_at", sa.String(50), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        )
        op.create_index("ix_identity_credentials_identity_id", "identity_credentials", ["identity_id"])

    if not _table_exists("sso_providers"):
        op.create_table(
            "sso_providers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("protocol", postgresql.ENUM("OAuth2", "OpenID Connect", "SAML", name="ssoprotocol", create_type=False), nullable=False),
            sa.Column("status", postgresql.ENUM("active", "inactive", "pending", name="ssoproviderstatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("connected_at", sa.String(50), nullable=False),
            sa.Column("last_sync", sa.String(50), nullable=True),
            sa.Column("users_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("region", sa.String(100), nullable=False, server_default=""),
        )

    if not _table_exists("sso_sessions"):
        op.create_table(
            "sso_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sso_providers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("ip_address", sa.String(100), nullable=False, server_default=""),
            sa.Column("device", sa.String(255), nullable=False, server_default=""),
            sa.Column("login_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", postgresql.ENUM("active", "expired", "revoked", name="ssosessionstatus", create_type=False), nullable=False, server_default="active"),
        )
        op.create_index("ix_sso_sessions_user_id", "sso_sessions", ["user_id"])

    if not _table_exists("consent_records"):
        op.create_table(
            "consent_records",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("app_name", sa.String(255), nullable=False),
            sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sso_providers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("scopes_granted", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("status", postgresql.ENUM("active", "revoked", name="consentstatus", create_type=False), nullable=False, server_default="active"),
        )
        op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"])

    if not _table_exists("fin_cards"):
        op.create_table(
            "fin_cards",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("holder_name", sa.String(255), nullable=False),
            sa.Column("card_number_masked", sa.String(25), nullable=False),
            sa.Column("card_type", postgresql.ENUM("virtual", "physical", "biometric", name="cardtype", create_type=False), nullable=False, server_default="virtual"),
            sa.Column("status", postgresql.ENUM("active", "frozen", "pending", "expired", "revoked", name="cardstatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("expires_at", sa.String(10), nullable=False),
            sa.Column("daily_limit", sa.Float(), nullable=False, server_default="50000"),
            sa.Column("monthly_limit", sa.Float(), nullable=False, server_default="500000"),
            sa.Column("current_spend", sa.Float(), nullable=False, server_default="0"),
            sa.Column("linked_identity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("digital_identities.id", ondelete="SET NULL"), nullable=True),
            sa.Column("tokenized", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("dynamic_cvv", sa.String(10), nullable=False, server_default="---"),
            sa.Column("issued_at", sa.String(20), nullable=False),
            sa.Column("biometric_bound", sa.Boolean(), nullable=False, server_default="false"),
        )
        op.create_index("ix_fin_cards_user_id", "fin_cards", ["user_id"])

    if not _table_exists("card_transactions"):
        op.create_table(
            "card_transactions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fin_cards.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", postgresql.ENUM("payment", "withdrawal", "transfer", "refund", name="transactiontype", create_type=False), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(10), nullable=False, server_default="ETB"),
            sa.Column("merchant", sa.String(255), nullable=False),
            sa.Column("status", postgresql.ENUM("completed", "pending", "failed", "flagged", name="transactionstatus", create_type=False), nullable=False, server_default="pending"),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("location", sa.String(255), nullable=False, server_default=""),
            sa.Column("offline", sa.Boolean(), nullable=False, server_default="false"),
        )
        op.create_index("ix_card_transactions_card_id", "card_transactions", ["card_id"])

    if not _table_exists("card_rules"):
        op.create_table(
            "card_rules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fin_cards.id", ondelete="CASCADE"), nullable=False),
            sa.Column("rule_name", sa.String(255), nullable=False),
            sa.Column("condition", sa.Text(), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        )
        op.create_index("ix_card_rules_card_id", "card_rules", ["card_id"])

    if not _table_exists("audit_log"):
        op.create_table(
            "audit_log",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("action", sa.String(255), nullable=False),
            sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("actor_name", sa.String(255), nullable=False, server_default="System"),
            sa.Column("target", sa.String(255), nullable=False, server_default=""),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("details", sa.Text(), nullable=False, server_default=""),
        )
        op.create_index("ix_audit_log_action", "audit_log", ["action"])
        op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])


def downgrade() -> None:
    for tbl in [
        "audit_log", "card_rules", "card_transactions", "fin_cards",
        "consent_records", "sso_sessions", "sso_providers",
        "identity_credentials", "identity_attributes", "digital_identities",
        "kyc_applications", "biometric_records", "refresh_tokens", "users",
    ]:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))

    for name in [
        "transactionstatus", "transactiontype", "cardtype", "cardstatus",
        "consentstatus", "ssosessionstatus", "ssoproviderstatus", "ssoprotocol",
        "identitystatus", "kycstatus", "risklevel", "biometricstatus",
        "biometrictype", "userrole",
    ]:
        op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))
