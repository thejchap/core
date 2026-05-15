"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def cannot_connect() -> None:
    """Stub for test_cannot_connect (port deferred)."""

@test.skip("pending tryke port")
async def cannot_connect_2() -> None:
    """Stub for test_cannot_connect_2 (port deferred)."""

@test.skip("pending tryke port")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry (port deferred)."""
