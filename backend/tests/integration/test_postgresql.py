from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.core.config import Settings
from app.db.session import create_database_engine


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASELINE_REVISION = "0001_persistence_baseline"


class IntegrationTestSettings(BaseSettings):
    """Settings used only by PostgreSQL integration tests."""

    test_database_url: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return a validated URL for the dedicated test database."""

    raw_url = IntegrationTestSettings().test_database_url.get_secret_value()

    try:
        parsed_url = make_url(raw_url)
    except ArgumentError as error:
        raise RuntimeError(
            "TEST_DATABASE_URL must be a valid SQLAlchemy URL."
        ) from error

    if parsed_url.drivername != "postgresql+psycopg":
        raise RuntimeError("TEST_DATABASE_URL must use postgresql+psycopg.")

    if not parsed_url.database or not parsed_url.database.endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL must target a database ending in _test.")

    if parsed_url.username != "deployguard":
        raise RuntimeError("TEST_DATABASE_URL must use the deployguard role.")

    return raw_url


@pytest.fixture(scope="session")
def postgresql_engine(
    test_database_url: str,
) -> Generator[Engine]:
    """Create an engine connected only to the test database."""

    settings = Settings(
        _env_file=None,
        database_url=test_database_url,
        database_pool_size=2,
        database_max_overflow=0,
        database_pool_timeout_seconds=5,
    )

    database_engine = create_database_engine(settings)

    try:
        yield database_engine
    finally:
        database_engine.dispose()


def test_postgresql_connection_uses_restricted_test_role(
    postgresql_engine: Engine,
) -> None:
    with postgresql_engine.connect() as connection:
        role = connection.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user,
                    current_setting(
                        'server_version_num'
                    )::integer AS server_version_num,
                    rolsuper AS is_superuser,
                    rolcreatedb AS can_create_database,
                    rolcreaterole AS can_create_role,
                    rolreplication AS can_replicate,
                    rolbypassrls AS can_bypass_rls
                FROM pg_catalog.pg_roles
                WHERE rolname = current_user
                """
            )
        ).one()

        schema_permissions = connection.execute(
            text(
                """
                SELECT
                    has_schema_privilege(
                        current_user,
                        'public',
                        'USAGE'
                    ) AS has_usage,
                    has_schema_privilege(
                        current_user,
                        'public',
                        'CREATE'
                    ) AS has_create
                """
            )
        ).one()

    assert role.database_name.endswith("_test")
    assert role.database_user == "deployguard"
    assert role.server_version_num // 10000 == 18
    assert role.is_superuser is False
    assert role.can_create_database is False
    assert role.can_create_role is False
    assert role.can_replicate is False
    assert role.can_bypass_rls is False
    assert schema_permissions.has_usage is True
    assert schema_permissions.has_create is True


def test_alembic_baseline_is_applied_idempotently(
    test_database_url: str,
    postgresql_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        test_database_url,
    )

    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    migration_scripts = ScriptDirectory.from_config(alembic_config)

    assert migration_scripts.get_current_head() == BASELINE_REVISION

    command.upgrade(
        alembic_config,
        "head",
    )
    command.upgrade(
        alembic_config,
        "head",
    )

    with postgresql_engine.connect() as connection:
        migration_context = MigrationContext.configure(connection)

        assert migration_context.get_current_revision() == BASELINE_REVISION
