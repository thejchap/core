"""Tryke skip-stubs for test_fan.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def generic_fan() -> None:
    """Stub for test_generic_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def configurable_speeds_fan() -> None:
    """Stub for test_configurable_speeds_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def configurable_speeds_fan_with_missing_config_value() -> None:
    """Stub for test_configurable_speeds_fan_with_missing_config_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def configurable_speeds_fan_with_bad_config_value() -> None:
    """Stub for test_configurable_speeds_fan_with_bad_config_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def ge_12730_fan() -> None:
    """Stub for test_ge_12730_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def jasco_14314_fan() -> None:
    """Stub for test_jasco_14314_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def inovelli_lzw36() -> None:
    """Stub for test_inovelli_lzw36."""


@test.skip("zwave_js: sibling test pending tryke port")
async def leviton_zw4sf_fan() -> None:
    """Stub for test_leviton_zw4sf_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def enbrighten_55258_zw4002_fan() -> None:
    """Stub for test_enbrighten_55258_zw4002_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def enbrighten_58446_zwa4013_fan() -> None:
    """Stub for test_enbrighten_58446_zwa4013_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_fan() -> None:
    """Stub for test_thermostat_fan."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_fan_without_off() -> None:
    """Stub for test_thermostat_fan_without_off."""


@test.skip("zwave_js: sibling test pending tryke port")
async def thermostat_fan_without_preset_modes() -> None:
    """Stub for test_thermostat_fan_without_preset_modes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def honeywell_39358_fan() -> None:
    """Stub for test_honeywell_39358_fan."""
