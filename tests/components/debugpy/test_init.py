"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def default() -> None:
    """Stub for test_default (port deferred)."""

@test.skip("pending tryke port")
async def wait_on_startup() -> None:
    """Stub for test_wait_on_startup (port deferred)."""

@test.skip("pending tryke port")
async def on_demand() -> None:
    """Stub for test_on_demand (port deferred)."""
