from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def create_database_engine(settings: Settings) -> Engine:
    """Create the PostgreSQL engine and connection pool."""

    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
    )


def create_session_factory(
    database_engine: Engine,
) -> sessionmaker[Session]:
    """Create database sessions bound to the supplied engine."""

    return sessionmaker(
        bind=database_engine,
        autoflush=False,
        expire_on_commit=False,
    )


engine = create_database_engine(get_settings())
session_factory = create_session_factory(engine)


def get_db_session() -> Generator[Session]:
    """Provide one database session and always close it afterward."""

    session = session_factory()

    try:
        yield session
    finally:
        session.close()
