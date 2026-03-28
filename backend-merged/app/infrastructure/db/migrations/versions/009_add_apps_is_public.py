"""Add app_registry.apps.is_public (idempotent).

ORM and 001 include this column; some DBs only received partial syncs (007/008)
without is_public, causing SELECT/INSERT failures.

Revision ID: 009_apps_is_public
Revises: 008_align_orm
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op


revision: str = "009_apps_is_public"
down_revision: Union[str, None] = "008_align_orm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS "
        "is_public BOOLEAN NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    """No-op: dropping a column in use is unsafe for shared environments."""
