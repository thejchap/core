"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def async_setup_entry_not_ready() -> None:
    """Stub for test_async_setup_entry_not_ready (port deferred)."""

@test.skip("pending tryke port")
async def async_setup_entry_auth_failed() -> None:
    """Stub for test_async_setup_entry_auth_failed (port deferred)."""

@test.skip("pending tryke port")
async def device_info() -> None:
    """Stub for test_device_info (port deferred)."""
