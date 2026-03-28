"""Ensure trust.profiles and biometric.records exist (idempotent).

Some databases reached a high Alembic revision without ever applying
001_initial_idaas_schema (e.g. volume from an older branch). This restores
the tables the ORM expects.

Revision ID: 011_ensure_trust_biometric
Revises: 010_public_approved_apps
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op


revision: str = "011_ensure_trust_biometric"
down_revision: Union[str, None] = "010_public_approved_apps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS trust")
    op.execute("CREATE SCHEMA IF NOT EXISTS biometric")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS trust.profiles (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE,
            trust_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            kyc_tier INTEGER NOT NULL DEFAULT 0,
            face_verified BOOLEAN NOT NULL DEFAULT false,
            voice_verified BOOLEAN NOT NULL DEFAULT false,
            digital_identity_active BOOLEAN NOT NULL DEFAULT false,
            factors JSONB NOT NULL DEFAULT '{}'::jsonb,
            last_evaluated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_trust_profiles_user_id ON trust.profiles (user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS biometric.records (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            type VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            liveness_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            spoof_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            quality_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            risk_level VARCHAR(20) NOT NULL DEFAULT 'medium',
            device_info JSONB,
            ip_address VARCHAR(100),
            biometric_data_url VARCHAR(512),
            biometric_hash VARCHAR(255),
            verified_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_biometric_records_user_id ON biometric.records (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_biometric_records_type ON biometric.records (type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_biometric_records_status ON biometric.records (status)"
    )


def downgrade() -> None:
    """No-op: do not drop tables that may be required by the app."""
