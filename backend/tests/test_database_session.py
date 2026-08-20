import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings
from app.db.base import Base
from app.db import session as session_module


VALID_DATABASE_URL = (
    "postgresql+psycopg://deployguard:placeholder@localhost:5432/deployguard"
)


def test_declarative_base_starts_without_business_tables() -> None:
    assert issubclass(Base, DeclarativeBase)
    assert not Base.metadata.tables


def test_create_database_engine_uses_approved_pool_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    fake_engine = session_module.engine

    def fake_create_engine(
        database_url: str,
        **options: object,
    ) -> Engine:
        captured["database_url"] = database_url
        captured.update(options)
        return fake_engine

    monkeypatch.setattr(
        session_module,
        "create_engine",
        fake_create_engine,
    )

    settings = Settings(
        _env_file=None,
        database_url=VALID_DATABASE_URL,
        database_pool_size=6,
        database_max_overflow=7,
        database_pool_timeout_seconds=8,
    )

    result = session_module.create_database_engine(settings)

    assert result is fake_engine
    assert captured == {
        "database_url": VALID_DATABASE_URL,
        "pool_pre_ping": True,
        "pool_size": 6,
        "max_overflow": 7,
        "pool_timeout": 8,
    }


def test_create_session_factory_uses_safe_session_options() -> None:
    factory = session_module.create_session_factory(
        session_module.engine,
    )

    assert factory.kw["bind"] is session_module.engine
    assert factory.kw["autoflush"] is False
    assert factory.kw["expire_on_commit"] is False


def test_get_db_session_always_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    fake_session = FakeSession()

    monkeypatch.setattr(
        session_module,
        "session_factory",
        lambda: fake_session,
    )

    dependency = session_module.get_db_session()

    assert next(dependency) is fake_session

    with pytest.raises(StopIteration):
        next(dependency)

    assert fake_session.closed is True
