"""Tryke skip-stubs for test_climate.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_v2() -> None:
    """Stub for test_thermostat_v2."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_v2_turn_on_after_off() -> None:
    """Stub for test_thermostat_v2_turn_on_after_off."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_turn_on_after_off_no_heat_cool_auto() -> None:
    """Stub for test_thermostat_turn_on_after_off_no_heat_cool_auto."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_turn_on_after_off_with_resume() -> None:
    """Stub for test_thermostat_turn_on_after_off_with_resume."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_different_endpoints() -> None:
    """Stub for test_thermostat_different_endpoints."""


@test.skip("zwave_js: sibling test pending tryke port")
async def setpoint_thermostat() -> None:
    """Stub for test_setpoint_thermostat."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_heatit_z_trm6() -> None:
    """Stub for test_thermostat_heatit_z_trm6."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_heatit_z_trm3_no_value() -> None:
    """Stub for test_thermostat_heatit_z_trm3_no_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_heatit_z_trm3() -> None:
    """Stub for test_thermostat_heatit_z_trm3."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_heatit_z_trm2fx() -> None:
    """Stub for test_thermostat_heatit_z_trm2fx."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_srt321_hrt4_zw() -> None:
    """Stub for test_thermostat_srt321_hrt4_zw."""


@test.skip("zwave_js: sibling test pending tryke port")
async def preset_and_no_setpoint() -> None:
    """Stub for test_preset_and_no_setpoint."""


@test.skip("zwave_js: sibling test pending tryke port")
async def temp_unit_fix() -> None:
    """Stub for test_temp_unit_fix."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_unknown_values() -> None:
    """Stub for test_thermostat_unknown_values."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_preset_mode_manufacturer_specific() -> None:
    """Stub for test_set_preset_mode_manufacturer_specific."""


@test.skip("zwave_js: sibling test pending tryke port")
async def preset_mode_mapped_to_unsupported_hvac_mode() -> None:
    """Stub for test_preset_mode_mapped_to_unsupported_hvac_mode."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_preset_mode_mapped_preset() -> None:
    """Stub for test_set_preset_mode_mapped_preset."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_preset_mode_none_while_in_hvac_mode() -> None:
    """Stub for test_set_preset_mode_none_while_in_hvac_mode."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_preset_mode_none_unmapped_preset() -> None:
    """Stub for test_set_preset_mode_none_unmapped_preset."""
