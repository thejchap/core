"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_entity() -> None:
    """Stub for test_climate_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_mode_heat() -> None:
    """Stub for test_set_hvac_mode_heat."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_mode_off() -> None:
    """Stub for test_set_hvac_mode_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_error_handling() -> None:
    """Stub for test_climate_error_handling."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_unavailable_on_update_error() -> None:
    """Stub for test_climate_unavailable_on_update_error."""

