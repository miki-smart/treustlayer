"""Sync identity.users columns with UserModel (idempotent for legacy DBs).

Older databases may be missing columns that current 001 + ORM define. Uses
PostgreSQL ADD COLUMN IF NOT EXISTS so fresh installs are unchanged.

Revision ID: 005_sync_identity_users_columns
Revises: 004_add_identity_user_avatar
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op


revision: str = "005_sync_identity_users_columns"
down_revision: Union[str, None] = "004_add_identity_user_avatar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # One statement per execute (reliable across drivers).
    statements = [
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50)",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS avatar VARCHAR(500)",
        """ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'user'""",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS password_reset_token_hash VARCHAR(255)",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS password_reset_expires_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS email_verification_token_hash VARCHAR(255)",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
        "ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
    ]
    for sql in statements:
        op.execute(sql)


def downgrade() -> None:
    """No-op: columns may predate this revision."""
    pass
