import pytest
from pydantic import ValidationError

from app.core.config import Settings


VALID_DATABASE_URL = (
    "postgresql+psycopg://deployguard:placeholder@localhost:5432/deployguard"
)


def make_settings(**overrides: object) -> Settings:
    """Build isolated settings without reading the local .env file."""

    values: dict[str, object] = {
        "database_url": VALID_DATABASE_URL,
    }
    values.update(overrides)

    return Settings(
        _env_file=None,
        **values,
    )


def test_database_settings_use_secure_defaults() -> None:
    settings = make_settings()

    assert settings.database_url.get_secret_value() == VALID_DATABASE_URL
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert settings.database_pool_timeout_seconds == 30
    assert "placeholder" not in repr(settings)
    assert "**********" in repr(settings.database_url)


@pytest.mark.parametrize(
    ("database_url", "expected_message"),
    [
        (
            "not a valid URL",
            "valid SQLAlchemy URL",
        ),
        (
            "sqlite:///deployguard.db",
            r"postgresql\+psycopg",
        ),
        (
            "postgresql+psycopg://deployguard@localhost",
            "database name",
        ),
    ],
)
def test_database_url_validation_rejects_invalid_values(
    database_url: str,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match=expected_message,
    ):
        make_settings(database_url=database_url)


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    [
        ("database_pool_size", 0),
        ("database_max_overflow", -1),
        ("database_pool_timeout_seconds", 0),
    ],
)
def test_database_pool_settings_reject_unsafe_values(
    field_name: str,
    unsafe_value: int,
) -> None:
    with pytest.raises(ValidationError):
        make_settings(
            **{field_name: unsafe_value},
        )
