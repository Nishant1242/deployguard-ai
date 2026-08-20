from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.models.tenant import Tenant


EXPECTED_COLUMNS = {
    "id",
    "slug",
    "display_name",
    "status",
    "created_at",
    "updated_at",
}

EXPECTED_CHECK_CONSTRAINTS = {
    "ck_tenants_slug_length",
    "ck_tenants_slug_lowercase",
    "ck_tenants_slug_format",
    "ck_tenants_display_name_not_blank",
    "ck_tenants_status",
}


def test_tenant_metadata_defines_approved_columns() -> None:
    table = Tenant.__table__

    assert table.name == "tenants"
    assert set(table.columns.keys()) == EXPECTED_COLUMNS

    assert table.columns.id.primary_key is True
    assert table.columns.id.type.python_type is UUID
    assert table.columns.id.default is not None
    assert table.columns.id.default.is_callable is True

    assert table.columns.slug.nullable is False
    assert table.columns.slug.type.length == 63

    assert table.columns.display_name.nullable is False
    assert table.columns.display_name.type.length == 120

    assert table.columns.status.nullable is False
    assert table.columns.status.type.length == 20
    assert table.columns.status.default.arg == "active"
    assert table.columns.status.server_default.arg == "active"

    assert table.columns.created_at.nullable is False
    assert table.columns.created_at.type.python_type is datetime
    assert table.columns.created_at.server_default is not None

    assert table.columns.updated_at.nullable is False
    assert table.columns.updated_at.type.python_type is datetime
    assert table.columns.updated_at.server_default is not None
    assert table.columns.updated_at.onupdate is not None


def test_tenant_metadata_defines_approved_constraints() -> None:
    table = Tenant.__table__

    check_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    unique_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert check_constraints == EXPECTED_CHECK_CONSTRAINTS
    assert "uq_tenants_slug" in unique_constraints
