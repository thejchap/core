"""Tryke skip stub for BlueMaestro sensor tests."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""
