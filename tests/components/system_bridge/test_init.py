"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def migration_minor_1_to_2() -> None:
    """Stub for test_migration_minor_1_to_2 (port deferred)."""

@test.skip("pending tryke port")
async def migration_minor_future_version() -> None:
    """Stub for test_migration_minor_future_version (port deferred)."""

@test.skip("pending tryke port")
async def setup_timeout() -> None:
    """Stub for test_setup_timeout (port deferred)."""

@test.skip("pending tryke port")
async def coordinator_get_data_timeout() -> None:
    """Stub for test_coordinator_get_data_timeout (port deferred)."""
