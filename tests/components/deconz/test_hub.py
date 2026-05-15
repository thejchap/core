"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def device_registry_entry() -> None:
    """Stub for test_device_registry_entry (port deferred)."""

@test.skip("snapshot test - port deferred")
async def connection_status_signalling() -> None:
    """Stub for test_connection_status_signalling (port deferred)."""

@test.skip("snapshot test - port deferred")
async def update_address() -> None:
    """Stub for test_update_address (port deferred)."""
