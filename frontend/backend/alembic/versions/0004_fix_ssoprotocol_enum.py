"""rename ssoprotocol enum values to snake_case so they match SQLAlchemy enum names

SQLAlchemy stores a Python str-enum using the member's NAME (not VALUE) when
using a native PostgreSQL ENUM column.  The original migration created the DB
enum with human-readable labels ('OAuth2', 'OpenID Connect', 'SAML'), but
the Python enum names are 'oauth2', 'openid_connect', 'saml', causing an
InvalidTextRepresentationError on insert.

This migration renames the DB labels to match the Python names.

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-27 00:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum_label_exists(type_name: str, label: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_enum e "
        "JOIN pg_type t ON e.enumtypid = t.oid "
        "WHERE t.typname = :type AND e.enumlabel = :label"
    ), {"type": type_name, "label": label}).fetchone()
    return result is not None


def upgrade() -> None:
    renames = [
        ("OAuth2",       "oauth2"),
        ("OpenID Connect", "openid_connect"),
        ("SAML",         "saml"),
    ]
    for old_label, new_label in renames:
        if _enum_label_exists("ssoprotocol", old_label):
            # ALTER TYPE ... RENAME VALUE does not support bind params — values are hardcoded
            op.execute(sa.text(f"ALTER TYPE ssoprotocol RENAME VALUE '{old_label}' TO '{new_label}'"))


def downgrade() -> None:
    renames = [
        ("oauth2",        "OAuth2"),
        ("openid_connect", "OpenID Connect"),
        ("saml",          "SAML"),
    ]
    for old_label, new_label in renames:
        if _enum_label_exists("ssoprotocol", old_label):
            op.execute(sa.text(f"ALTER TYPE ssoprotocol RENAME VALUE '{old_label}' TO '{new_label}'"))
