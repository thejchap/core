"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def forecast_daily() -> None:
    """Stub for test_forecast_daily (port deferred)."""

@test.skip("snapshot test - port deferred")
async def forecast_daily_with_some_previous_days_data() -> None:
    """Stub for test_forecast_daily_with_some_previous_days_data (port deferred)."""

@test.skip("snapshot test - port deferred")
async def get_environment_canada_raw_forecast_data() -> None:
    """Stub for test_get_environment_canada_raw_forecast_data (port deferred)."""
