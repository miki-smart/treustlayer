"""Sync app_registry.apps columns with AppModel (idempotent).

Legacy or partial DBs may lack columns the ORM inserts (e.g. logo_url).

Revision ID: 007_app_reg_sync
Revises: 006_sess_rt_cols
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op


revision: str = "007_app_reg_sync"
down_revision: Union[str, None] = "006_sess_rt_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE app_registry.apps ADD COLUMN IF NOT EXISTS logo_url VARCHAR(512)"
    )


def downgrade() -> None:
    pass
