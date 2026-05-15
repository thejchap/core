"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_empty() -> None:
    """Stub for test_setup_empty (port deferred)."""

@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def unload() -> None:
    """Stub for test_unload (port deferred)."""
