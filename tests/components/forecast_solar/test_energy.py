"""Tryke skip stub for test_energy.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def energy_solar_forecast() -> None:
    """Stub for test_energy_solar_forecast."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def energy_solar_forecast_filters_midnight_utc_zeros() -> None:
    """Stub for test_energy_solar_forecast_filters_midnight_utc_zeros."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def energy_solar_forecast_invalid_id() -> None:
    """Stub for test_energy_solar_forecast_invalid_id."""

