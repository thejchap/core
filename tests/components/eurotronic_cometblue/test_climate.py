"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_state() -> None:
    """Stub for test_climate_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_hvac_and_preset_states() -> None:
    """Stub for test_climate_hvac_and_preset_states."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def climate_preset_away_active() -> None:
    """Stub for test_climate_preset_away_active."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_preset_mode() -> None:
    """Stub for test_set_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_preset_mode_display_only_raises() -> None:
    """Stub for test_set_preset_mode_display_only_raises."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_turn_off() -> None:
    """Stub for test_turn_on_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_temperature_errors() -> None:
    """Stub for test_set_temperature_errors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_data_error_handling() -> None:
    """Stub for test_update_data_error_handling."""

