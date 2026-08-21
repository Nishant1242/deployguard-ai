from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.tenant import TenantCreate, TenantResponse


def test_tenant_create_accepts_valid_input_and_trims_display_name() -> None:
    request = TenantCreate(
        slug="acme-operations",
        display_name="  Acme Operations  ",
    )

    assert request.slug == "acme-operations"
    assert request.display_name == "Acme Operations"


@pytest.mark.parametrize(
    "slug",
    [
        "ab",
        "Uppercase",
        "invalid--slug",
        "-leading",
        "trailing-",
        "invalid_slug",
        "invalid slug",
        "a" * 64,
    ],
)
def test_tenant_create_rejects_invalid_slugs(slug: str) -> None:
    with pytest.raises(ValidationError):
        TenantCreate(
            slug=slug,
            display_name="Valid Tenant",
        )


@pytest.mark.parametrize(
    "display_name",
    [
        "",
        "   ",
        "x" * 121,
        123,
    ],
)
def test_tenant_create_rejects_invalid_display_names(
    display_name: object,
) -> None:
    with pytest.raises(ValidationError):
        TenantCreate(
            slug="valid-tenant",
            display_name=display_name,
        )


def test_tenant_create_rejects_server_controlled_fields() -> None:
    with pytest.raises(ValidationError) as captured_error:
        TenantCreate.model_validate(
            {
                "slug": "acme-operations",
                "display_name": "Acme Operations",
                "status": "suspended",
            }
        )

    assert captured_error.value.errors()[0]["type"] == "extra_forbidden"


def test_tenant_response_returns_only_public_fields() -> None:
    timestamp = datetime.now(UTC)
    tenant = SimpleNamespace(
        id=uuid4(),
        slug="acme-operations",
        display_name="Acme Operations",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
        internal_value="must-not-be-returned",
    )

    response = TenantResponse.model_validate(tenant)

    assert response.model_dump() == {
        "id": tenant.id,
        "slug": "acme-operations",
        "display_name": "Acme Operations",
        "status": "active",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
