from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Tenant
from app.schemas.tenant import TenantCreate


POSTGRESQL_UNIQUE_VIOLATION = "23505"
TENANT_SLUG_UNIQUE_CONSTRAINT = "uq_tenants_slug"


class DuplicateTenantSlugError(Exception):
    """Indicate that the requested tenant slug already exists."""


def _is_duplicate_tenant_slug(error: IntegrityError) -> bool:
    """Identify only the approved tenant-slug unique constraint."""

    original_error = error.orig
    diagnostic = getattr(original_error, "diag", None)

    return (
        getattr(original_error, "sqlstate", None) == POSTGRESQL_UNIQUE_VIOLATION
        and getattr(diagnostic, "constraint_name", None)
        == TENANT_SLUG_UNIQUE_CONSTRAINT
    )


def create_tenant(
    session: Session,
    request: TenantCreate,
) -> Tenant:
    """Create and commit one tenant in a single transaction."""

    tenant = Tenant(
        slug=request.slug,
        display_name=request.display_name,
    )

    try:
        session.add(tenant)
        session.flush()
        session.refresh(tenant)
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_duplicate_tenant_slug(error):
            raise DuplicateTenantSlugError from error

        raise
    except SQLAlchemyError:
        session.rollback()
        raise

    return tenant


def get_tenant_by_id(
    session: Session,
    tenant_id: UUID,
) -> Tenant | None:
    """Return one tenant by primary key when it exists."""

    return session.get(
        Tenant,
        tenant_id,
    )
