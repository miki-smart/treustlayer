"""
Add user roles, password-reset columns, and app API-key hash.

Revision ID: 002_add_roles_and_api_keys
Revises: 001_initial_schema
Create Date: 2026-03-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_add_roles_and_api_keys"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── identity.users ────────────────────────────────────────────────────────
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(30),
            nullable=False,
            server_default="user",
        ),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column("password_reset_token_hash", sa.String(255), nullable=True),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="identity",
    )

    # email verification
    op.add_column(
        "users",
        sa.Column("email_verification_token_hash", sa.String(255), nullable=True),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="identity",
    )

    # ── app_registry.apps ─────────────────────────────────────────────────────
    op.add_column(
        "apps",
        sa.Column("api_key_hash", sa.String(255), nullable=True),
        schema="app_registry",
    )
    op.create_index(
        "ix_app_registry_apps_api_key_hash",
        "apps",
        ["api_key_hash"],
        schema="app_registry",
    )
    op.add_column(
        "apps",
        sa.Column("owner_id", sa.String(255), nullable=True),
        schema="app_registry",
    )
    op.create_index(
        "ix_app_registry_apps_owner_id",
        "apps",
        ["owner_id"],
        schema="app_registry",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_app_registry_apps_owner_id",
        table_name="apps",
        schema="app_registry",
    )
    op.drop_column("apps", "owner_id", schema="app_registry")
    op.drop_index(
        "ix_app_registry_apps_api_key_hash",
        table_name="apps",
        schema="app_registry",
    )
    op.drop_column("apps", "api_key_hash", schema="app_registry")

    op.drop_column("users", "password_reset_expires_at", schema="identity")
    op.drop_column("users", "password_reset_token_hash", schema="identity")
    op.drop_column("users", "email_verification_expires_at", schema="identity")
    op.drop_column("users", "email_verification_token_hash", schema="identity")
    op.drop_column("users", "role", schema="identity")
