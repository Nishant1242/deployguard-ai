from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


TENANT_SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class TenantCreate(BaseModel):
    """Validate a request to create one tenant."""

    slug: str = Field(
        min_length=3,
        max_length=63,
        pattern=TENANT_SLUG_PATTERN,
    )
    display_name: str = Field(
        min_length=1,
        max_length=120,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, value: object) -> object:
        """Remove surrounding whitespace before validating the name."""

        if isinstance(value, str):
            return value.strip()

        return value


class TenantResponse(BaseModel):
    """Return the safe public representation of a tenant."""

    id: UUID
    slug: str
    display_name: str
    status: Literal["active", "suspended"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
