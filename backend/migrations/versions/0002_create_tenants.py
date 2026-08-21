"""Create the tenants table.

Revision ID: 0002_create_tenants
Revises: 0001_persistence_baseline
Create Date: 2026-08-20 18:57:55.167214
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_create_tenants"
down_revision: str | Sequence[str] | None = "0001_persistence_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="active", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(display_name) <> ''", name="ck_tenants_display_name_not_blank"
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="ck_tenants_slug_format"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended')", name="ck_tenants_status"
        ),
        sa.CheckConstraint(
            "char_length(slug) BETWEEN 3 AND 63", name="ck_tenants_slug_length"
        ),
        sa.CheckConstraint("slug = lower(slug)", name="ck_tenants_slug_lowercase"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )


def downgrade() -> None:
    """Reverse the migration."""

    op.drop_table("tenants")
