from collections.abc import Generator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import tenants as tenants_module
from app.db.session import get_db_session
from app.main import app
from app.services.tenant import DuplicateTenantSlugError


TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
TIMESTAMP = datetime(
    2026,
    8,
    20,
    12,
    0,
    tzinfo=UTC,
)


@pytest.fixture
def client() -> Generator[TestClient]:
    """Provide an API client without connecting to PostgreSQL."""

    fake_session = MagicMock(spec=Session)

    def override_get_db_session() -> Generator[Session]:
        yield fake_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_create_tenant_returns_created_public_tenant(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant = SimpleNamespace(
        id=TENANT_ID,
        slug="acme-operations",
        display_name="Acme Operations",
        status="active",
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
        internal_value="must-not-be-returned",
    )
    service_mock = MagicMock(return_value=tenant)
    monkeypatch.setattr(
        tenants_module,
        "create_tenant_service",
        service_mock,
    )

    response = client.post(
        "/api/v1/tenants",
        json={
            "slug": "acme-operations",
            "display_name": "Acme Operations",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(TENANT_ID),
        "slug": "acme-operations",
        "display_name": "Acme Operations",
        "status": "active",
        "created_at": "2026-08-20T12:00:00Z",
        "updated_at": "2026-08-20T12:00:00Z",
    }

    service_mock.assert_called_once()
    service_request = service_mock.call_args.args[1]
    assert service_request.slug == "acme-operations"
    assert service_request.display_name == "Acme Operations"


def test_create_tenant_returns_conflict_for_duplicate_slug(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_mock = MagicMock(
        side_effect=DuplicateTenantSlugError(),
    )
    monkeypatch.setattr(
        tenants_module,
        "create_tenant_service",
        service_mock,
    )

    response = client.post(
        "/api/v1/tenants",
        json={
            "slug": "acme-operations",
            "display_name": "Acme Operations",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "A tenant with this slug already exists."}


@pytest.mark.parametrize(
    "payload",
    [
        {
            "slug": "Uppercase",
            "display_name": "Valid Tenant",
        },
        {
            "slug": "valid-tenant",
            "display_name": "   ",
        },
        {
            "slug": "valid-tenant",
            "display_name": "Valid Tenant",
            "status": "suspended",
        },
    ],
)
def test_create_tenant_rejects_invalid_requests_before_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, str],
) -> None:
    service_mock = MagicMock()
    monkeypatch.setattr(
        tenants_module,
        "create_tenant_service",
        service_mock,
    )

    response = client.post(
        "/api/v1/tenants",
        json=payload,
    )

    assert response.status_code == 422
    service_mock.assert_not_called()
