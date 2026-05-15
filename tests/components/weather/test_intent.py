"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_weather() -> None:
    """Stub for test_get_weather (port deferred)."""

@test.skip("pending tryke port")
async def get_weather_wrong_name() -> None:
    """Stub for test_get_weather_wrong_name (port deferred)."""

@test.skip("pending tryke port")
async def get_weather_no_entities() -> None:
    """Stub for test_get_weather_no_entities (port deferred)."""
