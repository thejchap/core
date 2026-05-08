"""Tryke skip-stubs for test_climate.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def sequence_mappings() -> None:
    """Stub for test_sequence_mappings."""


@test.skip("zha: sibling test pending tryke port")
async def climate_local_temperature() -> None:
    """Stub for test_climate_local_temperature."""


@test.skip("zha: sibling test pending tryke port")
async def climate_hvac_action_running_state() -> None:
    """Stub for test_climate_hvac_action_running_state."""


@test.skip("zha: sibling test pending tryke port")
async def climate_hvac_action_pi_demand() -> None:
    """Stub for test_climate_hvac_action_pi_demand."""


@test.skip("zha: sibling test pending tryke port")
async def hvac_mode() -> None:
    """Stub for test_hvac_mode."""


@test.skip("zha: sibling test pending tryke port")
async def hvac_modes() -> None:
    """Stub for test_hvac_modes."""


@test.skip("zha: sibling test pending tryke port")
async def target_temperature() -> None:
    """Stub for test_target_temperature."""


@test.skip("zha: sibling test pending tryke port")
async def target_temperature_high() -> None:
    """Stub for test_target_temperature_high."""


@test.skip("zha: sibling test pending tryke port")
async def target_temperature_low() -> None:
    """Stub for test_target_temperature_low."""


@test.skip("zha: sibling test pending tryke port")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("zha: sibling test pending tryke port")
async def set_temperature_hvac_mode() -> None:
    """Stub for test_set_temperature_hvac_mode."""


@test.skip("zha: sibling test pending tryke port")
async def set_temperature_heat_cool() -> None:
    """Stub for test_set_temperature_heat_cool."""


@test.skip("zha: sibling test pending tryke port")
async def set_temperature_heat() -> None:
    """Stub for test_set_temperature_heat."""


@test.skip("zha: sibling test pending tryke port")
async def set_temperature_cool() -> None:
    """Stub for test_set_temperature_cool."""


@test.skip("zha: sibling test pending tryke port")
async def set_temperature_wrong_mode() -> None:
    """Stub for test_set_temperature_wrong_mode."""


@test.skip("zha: sibling test pending tryke port")
async def fan_mode() -> None:
    """Stub for test_fan_mode."""


@test.skip("zha: sibling test pending tryke port")
async def set_fan_mode_not_supported() -> None:
    """Stub for test_set_fan_mode_not_supported."""


@test.skip("zha: sibling test pending tryke port")
async def set_fan_mode() -> None:
    """Stub for test_set_fan_mode."""
