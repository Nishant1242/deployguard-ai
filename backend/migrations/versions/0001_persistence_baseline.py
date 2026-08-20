"""Establish the PostgreSQL persistence baseline.

Revision ID: 0001_persistence_baseline
Revises:
Create Date: 2026-08-20
"""

from collections.abc import Sequence


revision: str = "0001_persistence_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the empty persistence baseline."""

    pass


def downgrade() -> None:
    """Reverse the empty persistence baseline."""

    pass
