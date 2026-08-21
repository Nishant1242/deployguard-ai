from collections.abc import Generator
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.main import app
from app.models import Tenant


@pytest.fixture
def database_client(
    database_session: Session,
) -> Generator[TestClient]:
    """Provide an API client connected to the rollback-isolated database."""

    def override_get_db_session() -> Generator[Session]:
        yield database_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def unique_slug(prefix: str) -> str:
    """Create a valid slug unique to one integration test."""

    return f"{prefix}-{uuid4().hex[:12]}"


def test_create_tenant_api_persists_public_tenant(
    database_client: TestClient,
    database_session: Session,
) -> None:
    slug = unique_slug("api-tenant")

    response = database_client.post(
        "/api/v1/tenants",
        json={
            "slug": slug,
            "display_name": "  Acme Operations  ",
        },
    )

    assert response.status_code == 201

    response_body = response.json()

    assert set(response_body) == {
        "id",
        "slug",
        "display_name",
        "status",
        "created_at",
        "updated_at",
    }
    assert UUID(response_body["id"])
    assert response_body["slug"] == slug
    assert response_body["display_name"] == "Acme Operations"
    assert response_body["status"] == "active"

    created_at = datetime.fromisoformat(
        response_body["created_at"].replace("Z", "+00:00")
    )
    updated_at = datetime.fromisoformat(
        response_body["updated_at"].replace("Z", "+00:00")
    )

    assert created_at.tzinfo is not None
    assert updated_at.tzinfo is not None

    persisted_tenant = database_session.scalar(
        select(Tenant).where(Tenant.slug == slug)
    )

    assert persisted_tenant is not None
    assert persisted_tenant.id == UUID(response_body["id"])
    assert persisted_tenant.display_name == "Acme Operations"
    assert persisted_tenant.status == "active"


def test_create_tenant_api_returns_conflict_and_recovers_session(
    database_client: TestClient,
    database_session: Session,
) -> None:
    slug = unique_slug("api-duplicate")

    first_response = database_client.post(
        "/api/v1/tenants",
        json={
            "slug": slug,
            "display_name": "First Tenant",
        },
    )
    duplicate_response = database_client.post(
        "/api/v1/tenants",
        json={
            "slug": slug,
            "display_name": "Duplicate Tenant",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "A tenant with this slug already exists."
    }

    tenant_count = database_session.scalar(
        select(func.count()).select_from(Tenant).where(Tenant.slug == slug)
    )

    assert tenant_count == 1


def test_get_tenant_api_retrieves_existing_tenant_from_postgresql(
    database_client: TestClient,
    database_session: Session,
) -> None:
    slug = unique_slug("api-retrieve")
    tenant = Tenant(
        slug=slug,
        display_name="Retrieved Tenant",
        status="suspended",
    )

    database_session.add(tenant)
    database_session.flush()

    tenant_id = tenant.id
    database_session.expunge_all()

    response = database_client.get(
        f"/api/v1/tenants/{tenant_id}",
    )

    assert response.status_code == 200

    response_body = response.json()

    assert set(response_body) == {
        "id",
        "slug",
        "display_name",
        "status",
        "created_at",
        "updated_at",
    }
    assert response_body["id"] == str(tenant_id)
    assert response_body["slug"] == slug
    assert response_body["display_name"] == "Retrieved Tenant"
    assert response_body["status"] == "suspended"

    created_at = datetime.fromisoformat(
        response_body["created_at"].replace("Z", "+00:00")
    )
    updated_at = datetime.fromisoformat(
        response_body["updated_at"].replace("Z", "+00:00")
    )

    assert created_at.tzinfo is not None
    assert updated_at.tzinfo is not None


def test_get_tenant_api_returns_not_found_for_unknown_uuid(
    database_client: TestClient,
) -> None:
    missing_tenant_id = uuid4()

    response = database_client.get(
        f"/api/v1/tenants/{missing_tenant_id}",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Tenant not found."}
