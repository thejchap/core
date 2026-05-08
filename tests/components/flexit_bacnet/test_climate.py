"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_entity() -> None:
    """Stub for test_climate_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_preset_mode() -> None:
    """Stub for test_set_hvac_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hvac_action() -> None:
    """Stub for test_hvac_action."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""

