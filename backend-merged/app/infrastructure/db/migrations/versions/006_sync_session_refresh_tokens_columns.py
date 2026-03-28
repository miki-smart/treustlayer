"""Add session.refresh_tokens columns expected by RefreshTokenModel (idempotent).

Databases created from 001 only, or where 002 did not apply, lack device_info,
ip_address, last_used_at. ORM always selects these columns.

Revision ID: 006_sess_rt_cols (≤32 chars for alembic_version.version_num)
Revises: 005_sync_identity_users_columns
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op


revision: str = "006_sess_rt_cols"
down_revision: Union[str, None] = "005_sync_identity_users_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    statements = [
        "ALTER TABLE session.refresh_tokens ADD COLUMN IF NOT EXISTS device_info VARCHAR(500)",
        "ALTER TABLE session.refresh_tokens ADD COLUMN IF NOT EXISTS ip_address VARCHAR(50)",
        "ALTER TABLE session.refresh_tokens ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP WITH TIME ZONE",
    ]
    for sql in statements:
        op.execute(sql)


def downgrade() -> None:
    """No-op: columns may predate this revision or match 002."""
    pass
