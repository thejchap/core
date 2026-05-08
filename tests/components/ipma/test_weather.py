"""Tryke skip-stubs for test_weather.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def setup_config_flow() -> None:
    """Stub for test_setup_config_flow."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def failed_get_observation_forecast() -> None:
    """Stub for test_failed_get_observation_forecast."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def forecast_service() -> None:
    """Stub for test_forecast_service."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def forecast_subscription() -> None:
    """Stub for test_forecast_subscription."""
