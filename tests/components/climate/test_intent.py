"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def set_temperature() -> None:
    """Stub for test_set_temperature (port deferred)."""

@test.skip("pending tryke port")
async def set_temperature_no_entities() -> None:
    """Stub for test_set_temperature_no_entities (port deferred)."""

@test.skip("pending tryke port")
async def set_temperature_not_supported() -> None:
    """Stub for test_set_temperature_not_supported (port deferred)."""
