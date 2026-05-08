"""Tryke skip-stubs for meteo_lt weather tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def weather_placeholder() -> None:
    """Placeholder skipped sibling tests for test_weather.py."""
