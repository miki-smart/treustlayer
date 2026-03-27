"""add extracted_data to kyc_applications

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-27 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column}).fetchone()
    return result is not None


def upgrade() -> None:
    if not _column_exists("kyc_applications", "extracted_data"):
        op.add_column(
            "kyc_applications",
            sa.Column("extracted_data", postgresql.JSONB(), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("kyc_applications", "extracted_data"):
        op.drop_column("kyc_applications", "extracted_data")
