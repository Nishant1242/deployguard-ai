from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import Tenant
from app.schemas.tenant import TenantCreate, TenantResponse
from app.services.tenant import (
    DuplicateTenantSlugError,
    create_tenant as create_tenant_service,
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
