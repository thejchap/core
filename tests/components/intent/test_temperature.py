"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_temperature() -> None:
    """Stub for test_get_temperature (port deferred)."""

@test.skip("pending tryke port")
async def get_temperature_no_entities() -> None:
    """Stub for test_get_temperature_no_entities (port deferred)."""

@test.skip("pending tryke port")
async def not_exposed() -> None:
    """Stub for test_not_exposed (port deferred)."""
