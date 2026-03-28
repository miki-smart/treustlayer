"""Align DB schema with SQLAlchemy models (idempotent).

Fixes legacy / partial databases where alembic version is current but columns
or tables are missing (e.g. apps.category, consent.consent_records, KYC columns).

Revision ID: 008_align_orm
Revises: 007_app_reg_sync
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op


revision: str = "008_align_orm"
down_revision: Union[str, None] = "007_app_reg_sync"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS consent")
    op.execute("CREATE SCHEMA IF NOT EXISTS kyc")

    # --- app_registry.apps (AppModel) ---
    app_cols = [
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS category VARCHAR(50) NOT NULL DEFAULT 'general'",
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS logo_url VARCHAR(512)",
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT false",
    ]
    for sql in app_cols:
        op.execute(sql)

    # --- consent: ORM uses consent_records; some DBs still have consents from 001 only ---
    op.execute(
        """
        DO $c$
        BEGIN
            IF to_regclass('consent.consent_records') IS NULL THEN
                IF to_regclass('consent.consents') IS NOT NULL THEN
                    ALTER TABLE consent.consents RENAME TO consent_records;
                ELSE
                    CREATE TABLE consent.consent_records (
                        id UUID PRIMARY KEY,
                        user_id UUID NOT NULL,
                        client_id VARCHAR(120) NOT NULL,
                        scopes VARCHAR[] NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT true,
                        granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        revoked_at TIMESTAMP WITH TIME ZONE
                    );
                    CREATE INDEX IF NOT EXISTS ix_consent_records_user_id ON consent.consent_records (user_id);
                    CREATE INDEX IF NOT EXISTS ix_consent_records_client_id ON consent.consent_records (client_id);
                END IF;
            END IF;
        END
        $c$;
        """
    )

    # --- kyc.verifications (KYCModel): minimal / old tables may omit columns from 001 ---
    kyc_cols = [
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS date_of_birth DATE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS gender VARCHAR(20)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS nationality VARCHAR(100)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS place_of_birth VARCHAR(255)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS document_type VARCHAR(100)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS document_number VARCHAR(100)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS issue_date DATE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS expiry_date DATE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS address TEXT",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS billing_name VARCHAR(255)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS service_provider VARCHAR(255)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS service_type VARCHAR(100)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS bill_date DATE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS account_number VARCHAR(100)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS mrz_line1 VARCHAR(255)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS mrz_line2 VARCHAR(255)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS id_front_url VARCHAR(512)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS id_back_url VARCHAR(512)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS utility_bill_url VARCHAR(512)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS face_image_url VARCHAR(512)",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS documents_submitted JSONB DEFAULT '[]'::jsonb",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS extracted_data JSONB",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS id_ocr_confidence DOUBLE PRECISION DEFAULT 0.0",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS utility_ocr_confidence DOUBLE PRECISION DEFAULT 0.0",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS overall_confidence DOUBLE PRECISION DEFAULT 0.0",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS risk_score INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS synthetic_id_probability DOUBLE PRECISION DEFAULT 0.0",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS face_similarity_score DOUBLE PRECISION",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS reviewer_id UUID",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS rejection_reason TEXT",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
        "ALTER TABLE kyc.verifications ADD COLUMN IF NOT EXISTS tier VARCHAR(20) NOT NULL DEFAULT 'tier_0'",
    ]
    for sql in kyc_cols:
        op.execute(sql)


def downgrade() -> None:
    """No-op: alignment is additive and safe to keep."""
