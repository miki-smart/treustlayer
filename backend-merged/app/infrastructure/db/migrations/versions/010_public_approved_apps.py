"""Backfill is_public for already-approved apps (marketplace visibility).

Approved apps should appear in GET /apps/marketplace; older rows may have
is_approved=true and is_public=false.

Revision ID: 010_public_approved_apps
Revises: 009_apps_is_public
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op


revision: str = "010_public_approved_apps"
down_revision: Union[str, None] = "009_apps_is_public"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE app_registry.apps SET is_public = true "
        "WHERE is_approved = true AND is_public = false"
    )


def downgrade() -> None:
    """Cannot know prior is_public intent; no-op."""
