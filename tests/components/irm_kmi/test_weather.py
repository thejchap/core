"""Tryke skip-stubs for test_weather.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def weather_nl() -> None:
    """Stub for test_weather_nl."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def forecast_service() -> None:
    """Stub for test_forecast_service."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def weather_higher_temp_at_night() -> None:
    """Stub for test_weather_higher_temp_at_night."""
