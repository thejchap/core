"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_get_state() -> None:
    """Stub for test_climate_get_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_set_off() -> None:
    """Stub for test_climate_set_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_set_unsupported_hvac_mode() -> None:
    """Stub for test_climate_set_unsupported_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_set_temperature() -> None:
    """Stub for test_climate_set_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_set_temperature_unsupported_hvac_mode() -> None:
    """Stub for test_climate_set_temperature_unsupported_hvac_mode."""

