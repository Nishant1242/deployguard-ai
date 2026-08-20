from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    """Represent one customer organization in DeployGuard AI."""

    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint(
            "slug",
            name="uq_tenants_slug",
        ),
        CheckConstraint(
            "char_length(slug) BETWEEN 3 AND 63",
            name="ck_tenants_slug_length",
        ),
        CheckConstraint(
            "slug = lower(slug)",
            name="ck_tenants_slug_lowercase",
        ),
        CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="ck_tenants_slug_format",
        ),
        CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_tenants_display_name_not_blank",
        ),
        CheckConstraint(
            "status IN ('active', 'suspended')",
            name="ck_tenants_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(63),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
