from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import Tenant


@pytest.fixture
def database_session(
    migrated_postgresql_engine: Engine,
) -> Generator[Session]:
    """Provide a transaction that is rolled back after each test."""

    connection = migrated_postgresql_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


def unique_slug(prefix: str) -> str:
    """Create a valid slug that is unique for one test run."""

    return f"{prefix}-{uuid4().hex[:12]}"


def test_tenant_is_persisted_with_database_defaults(
    database_session: Session,
) -> None:
    tenant = Tenant(
        slug=unique_slug("tenant"),
        display_name="Stable Rock Solutions",
    )

    database_session.add(tenant)
    database_session.flush()

    tenant_id = tenant.id
    database_session.expire_all()

    persisted_tenant = database_session.scalar(
        select(Tenant).where(Tenant.id == tenant_id)
    )

    assert persisted_tenant is not None
    assert isinstance(persisted_tenant.id, UUID)
    assert persisted_tenant.status == "active"
    assert persisted_tenant.created_at is not None
    assert persisted_tenant.created_at.tzinfo is not None
    assert persisted_tenant.updated_at is not None
    assert persisted_tenant.updated_at.tzinfo is not None


def test_tenant_accepts_suspended_status(
    database_session: Session,
) -> None:
    tenant = Tenant(
        slug=unique_slug("suspended"),
        display_name="Suspended Tenant",
        status="suspended",
    )

    database_session.add(tenant)
    database_session.flush()

    assert tenant.status == "suspended"


def test_tenant_slug_must_be_unique(
    database_session: Session,
) -> None:
    slug = unique_slug("duplicate")

    database_session.add(
        Tenant(
            slug=slug,
            display_name="First Tenant",
        )
    )
    database_session.flush()

    database_session.add(
        Tenant(
            slug=slug,
            display_name="Second Tenant",
        )
    )

    with pytest.raises(IntegrityError):
        database_session.flush()


@pytest.mark.parametrize(
    (
        "slug",
        "display_name",
        "status",
    ),
    [
        (
            "ab",
            "Valid Tenant",
            "active",
        ),
        (
            "Uppercase",
            "Valid Tenant",
            "active",
        ),
        (
            "invalid--slug",
            "Valid Tenant",
            "active",
        ),
        (
            "a" * 64,
            "Valid Tenant",
            "active",
        ),
        (
            "valid-slug",
            "   ",
            "active",
        ),
        (
            "valid-slug",
            "x" * 121,
            "active",
        ),
        (
            "valid-slug",
            "Valid Tenant",
            "deleted",
        ),
    ],
)
def test_tenant_constraints_reject_invalid_values(
    database_session: Session,
    slug: str,
    display_name: str,
    status: str,
) -> None:
    database_session.add(
        Tenant(
            slug=slug,
            display_name=display_name,
            status=status,
        )
    )

    with pytest.raises((DataError, IntegrityError)):
        database_session.flush()
