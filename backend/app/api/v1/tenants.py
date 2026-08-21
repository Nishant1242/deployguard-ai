from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import Tenant
from app.schemas.tenant import TenantCreate, TenantResponse
from app.services.tenant import (
    DuplicateTenantSlugError,
    create_tenant as create_tenant_service,
    get_tenant_by_id,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Tenants"],
)


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "The tenant slug already exists.",
        }
    },
)
def create_tenant(
    request: TenantCreate,
    session: Annotated[Session, Depends(get_db_session)],
) -> Tenant:
    """Create one tenant organization."""

    try:
        return create_tenant_service(
            session,
            request,
        )
    except DuplicateTenantSlugError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tenant with this slug already exists.",
        ) from error


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "The tenant does not exist.",
        }
    },
)
def get_tenant(
    tenant_id: UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> Tenant:
    """Return one tenant organization by UUID."""

    tenant = get_tenant_by_id(
        session,
        tenant_id,
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return tenant
