"""Test for the smhi weather entity. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup_hass() -> None:
    """Stub for test_setup_hass (port deferred)."""

@test.skip("syrupy snapshot")
async def clear_night() -> None:
    """Stub for test_clear_night (port deferred)."""

@test.skip("syrupy snapshot")
async def properties_no_data() -> None:
    """Stub for test_properties_no_data (port deferred)."""

@test.skip("syrupy snapshot")
async def properties_unknown_symbol() -> None:
    """Stub for test_properties_unknown_symbol (port deferred)."""

@test.skip("syrupy snapshot")
async def refresh_weather_forecast_retry() -> None:
    """Stub for test_refresh_weather_forecast_retry (port deferred)."""

@test.skip("syrupy snapshot")
async def condition_class() -> None:
    """Stub for test_condition_class (port deferred)."""

@test.skip("syrupy snapshot")
async def custom_speed_unit() -> None:
    """Stub for test_custom_speed_unit (port deferred)."""

@test.skip("syrupy snapshot")
async def forecast_services() -> None:
    """Stub for test_forecast_services (port deferred)."""

@test.skip("syrupy snapshot")
async def forecast_services_lack_of_data() -> None:
    """Stub for test_forecast_services_lack_of_data (port deferred)."""

@test.skip("syrupy snapshot")
async def forecast_service() -> None:
    """Stub for test_forecast_service (port deferred)."""

@test.skip("syrupy snapshot")
async def twice_daily_forecast_service() -> None:
    """Stub for test_twice_daily_forecast_service (port deferred)."""
