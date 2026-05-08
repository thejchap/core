"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_heater() -> None:
    """Stub for test_setup_heater."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dynamic_new_devices() -> None:
    """Stub for test_dynamic_new_devices."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_preset_mode() -> None:
    """Stub for test_set_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_update() -> None:
    """Stub for test_state_update."""

