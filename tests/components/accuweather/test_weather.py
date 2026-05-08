"""Tryke skip stub for test_weather.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def weather() -> None:
    """Stub for test_weather."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def unsupported_condition_icon_data() -> None:
    """Stub for test_unsupported_condition_icon_data."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def forecast_service() -> None:
    """Stub for test_forecast_service."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def forecast_daily_missing_average_humidity() -> None:
    """Stub for test_forecast_daily_missing_average_humidity."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def forecast_subscription() -> None:
    """Stub for test_forecast_subscription."""


