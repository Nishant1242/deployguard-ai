from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.tenant import TenantCreate
from app.services.tenant import (
    DuplicateTenantSlugError,
    create_tenant,
)


class FakeDiagnostic:
    """Provide the PostgreSQL diagnostic value used by the service."""

    def __init__(self, constraint_name: str) -> None:
        self.constraint_name = constraint_name


class FakeOriginalError(Exception):
    """Provide PostgreSQL error information without a real database."""

    def __init__(
        self,
        sqlstate: str,
        constraint_name: str,
    ) -> None:
        super().__init__("database error")
        self.sqlstate = sqlstate
        self.diag = FakeDiagnostic(constraint_name)


def make_integrity_error(
    *,
    sqlstate: str = "23505",
    constraint_name: str = "uq_tenants_slug",
) -> IntegrityError:
    """Create a SQLAlchemy integrity error for one unit test."""

    return IntegrityError(
        "INSERT INTO tenants",
        {},
        FakeOriginalError(
            sqlstate=sqlstate,
            constraint_name=constraint_name,
        ),
    )


def tenant_request() -> TenantCreate:
    """Create one valid tenant request."""

    return TenantCreate(
        slug="acme-operations",
        display_name="Acme Operations",
    )


def test_create_tenant_commits_and_returns_tenant() -> None:
    session = MagicMock(spec=Session)

    tenant = create_tenant(
        session,
        tenant_request(),
    )

    assert tenant.slug == "acme-operations"
    assert tenant.display_name == "Acme Operations"
    session.add.assert_called_once_with(tenant)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(tenant)
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


def test_create_tenant_maps_slug_constraint_to_domain_error() -> None:
    session = MagicMock(spec=Session)
    session.flush.side_effect = make_integrity_error()

    with pytest.raises(DuplicateTenantSlugError):
        create_tenant(
            session,
            tenant_request(),
        )

    session.rollback.assert_called_once_with()
    session.refresh.assert_not_called()
    session.commit.assert_not_called()


def test_create_tenant_reraises_other_integrity_errors() -> None:
    session = MagicMock(spec=Session)
    database_error = make_integrity_error(
        constraint_name="ck_tenants_status",
    )
    session.flush.side_effect = database_error

    with pytest.raises(IntegrityError) as captured_error:
        create_tenant(
            session,
            tenant_request(),
        )

    assert captured_error.value is database_error
    session.rollback.assert_called_once_with()
    session.refresh.assert_not_called()
    session.commit.assert_not_called()


def test_create_tenant_rolls_back_other_database_errors() -> None:
    session = MagicMock(spec=Session)
    database_error = SQLAlchemyError("database unavailable")
    session.commit.side_effect = database_error

    with pytest.raises(SQLAlchemyError) as captured_error:
        create_tenant(
            session,
            tenant_request(),
        )

    assert captured_error.value is database_error
    session.rollback.assert_called_once_with()
