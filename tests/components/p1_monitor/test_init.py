"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry (port deferred)."""

@test.skip("snapshot test - port deferred")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready (port deferred)."""

@test.skip("snapshot test - port deferred")
async def migration() -> None:
    """Stub for test_migration (port deferred)."""

@test.skip("snapshot test - port deferred")
async def port_migration() -> None:
    """Stub for test_port_migration (port deferred)."""
