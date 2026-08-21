import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text


CURRENT_REVISION = "0002_create_tenants"


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


def test_alembic_head_is_applied_idempotently(
    test_database_url: str,
    migrated_postgresql_engine: Engine,
    alembic_config: Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        test_database_url,
    )

    migration_scripts = ScriptDirectory.from_config(alembic_config)

    assert migration_scripts.get_current_head() == CURRENT_REVISION

    command.upgrade(
        alembic_config,
        "head",
    )
    command.upgrade(
        alembic_config,
        "head",
    )

    with migrated_postgresql_engine.connect() as connection:
        migration_context = MigrationContext.configure(connection)

        assert migration_context.get_current_revision() == CURRENT_REVISION
