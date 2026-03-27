"""add_next_schema_changes

Revision ID: 003_add_next_schema_changes
Revises: 002_add_roles_and_api_keys
Create Date: 2026-03-27 18:06:30.276574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_add_next_schema_changes"
down_revision: Union[str, None] = "002_add_roles_and_api_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
