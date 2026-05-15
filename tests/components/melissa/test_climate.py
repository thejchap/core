"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def setup_platform() -> None:
    """Stub for test_setup_platform (port deferred)."""

@test.skip("snapshot test - port deferred")
async def actions() -> None:
    """Stub for test_actions (port deferred)."""
