"""Tryke skip-stubs for met weather tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def weather_placeholder() -> None:
    """Placeholder skipped sibling tests for test_weather.py."""
