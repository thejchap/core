"""Tryke skip stub for test_weather.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def attributes() -> None:
    """Stub for test_attributes."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def forecast() -> None:
    """Stub for test_forecast."""

