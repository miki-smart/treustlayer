"""Add identity.users.avatar when missing (ORM / newer 001 include this column).

Revision ID: 004_add_identity_user_avatar
Revises: 003_add_next_schema_changes
Create Date: 2026-03-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "004_add_identity_user_avatar"
down_revision: Union[str, None] = "003_add_next_schema_changes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_avatar_column() -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = insp.get_columns("users", schema="identity")
    return any(c["name"] == "avatar" for c in cols)


def upgrade() -> None:
    if not _has_avatar_column():
        op.add_column(
            "users",
            sa.Column("avatar", sa.String(500), nullable=True),
            schema="identity",
        )


def downgrade() -> None:
    """Intentional no-op: `avatar` may already exist from 001; avoid dropping shared columns."""
    pass
