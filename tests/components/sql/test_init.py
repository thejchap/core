"""Tryke skip-stubs for SQL test_init."""

from tryke import test


@test.skip("requires recorder + integration setup — port deferred")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("requires recorder + integration setup — port deferred")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("requires recorder + YAML import flow — port deferred")
async def setup_config() -> None:
    """Stub for test_setup_config."""


@test.skip("requires recorder + invalid-config flow — port deferred")
async def setup_invalid_config() -> None:
    """Stub for test_setup_invalid_config."""


@test.skip("requires schema validation context — port deferred")
async def invalid_query() -> None:
    """Stub for test_invalid_query."""


@test.skip("requires schema validation context — port deferred")
async def query_no_read_only() -> None:
    """Stub for test_query_no_read_only."""


@test.skip("requires schema validation context — port deferred")
async def query_no_read_only_cte() -> None:
    """Stub for test_query_no_read_only_cte."""


@test.skip("requires schema validation context — port deferred")
async def multiple_queries() -> None:
    """Stub for test_multiple_queries."""


@test.skip("requires recorder + schema migration — port deferred")
async def migration_from_future() -> None:
    """Stub for test_migration_from_future."""


@test.skip("requires recorder + schema migration — port deferred")
async def migration_from_v1_to_v2() -> None:
    """Stub for test_migration_from_v1_to_v2."""
