import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.db.session import create_database_engine
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[3]


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


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    """Create Alembic configuration from the repository root."""

    return Config(str(PROJECT_ROOT / "alembic.ini"))


@pytest.fixture(scope="session")
def migrated_postgresql_engine(
    test_database_url: str,
    postgresql_engine: Engine,
    alembic_config: Config,
) -> Engine:
    """Upgrade the dedicated test database before model tests."""

    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_database_url

    try:
        command.upgrade(
            alembic_config,
            "head",
        )
    finally:
        if previous_database_url is None:
            os.environ.pop(
                "DATABASE_URL",
                None,
            )
        else:
            os.environ["DATABASE_URL"] = previous_database_url

    return postgresql_engine


@pytest.fixture
def database_session(
    migrated_postgresql_engine: Engine,
) -> Generator[Session]:
    """Provide a rollback-isolated session that supports service commits."""

    connection = migrated_postgresql_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()
