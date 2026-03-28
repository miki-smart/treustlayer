"""Ensure digital_identity schema and identities/attributes/credentials exist (idempotent).

Same rationale as 011_ensure_trust_biometric: some DB volumes never applied 001 fully.

Revision ID: 012_ensure_digital_identity
Revises: 011_ensure_trust_biometric
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "012_ensure_digital_identity"
down_revision: Union[str, None] = "011_ensure_trust_biometric"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS digital_identity")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS digital_identity.identities (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE,
            unique_id VARCHAR(500) NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_verified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_digital_identities_user_id "
        "ON digital_identity.identities (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_digital_identities_unique_id "
        "ON digital_identity.identities (unique_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS digital_identity.attributes (
            id UUID PRIMARY KEY,
            identity_id UUID NOT NULL,
            key VARCHAR(255) NOT NULL,
            value TEXT NOT NULL,
            is_shared BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_identity_attributes_identity_id "
        "ON digital_identity.attributes (identity_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS digital_identity.credentials (
            id UUID PRIMARY KEY,
            identity_id UUID NOT NULL,
            type VARCHAR(255) NOT NULL,
            issuer VARCHAR(255) NOT NULL,
            credential_data JSONB NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            issued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_identity_credentials_identity_id "
        "ON digital_identity.credentials (identity_id)"
    )


def downgrade() -> None:
    """No-op: do not drop tables that may be required by the app."""
