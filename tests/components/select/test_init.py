"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def select() -> None:
    """Stub for test_select (port deferred)."""

@test.skip("pending tryke port")
async def custom_integration_and_validation() -> None:
    """Stub for test_custom_integration_and_validation (port deferred)."""
