"""Tryke skip-stubs for test_climate.py - indirect parametrize unsupported."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the home_connect integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.home_connect.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("home_connect")


@test.skip("indirect parametrize unsupported")
async def paired_depaired_devices_flow() -> None:
    """Stub for test_paired_depaired_devices_flow."""

@test.skip("indirect parametrize unsupported")
async def connected_devices() -> None:
    """Stub for test_connected_devices."""

@test.skip("indirect parametrize unsupported")
async def climate_entity_availability() -> None:
    """Stub for test_climate_entity_availability."""

@test.skip("indirect parametrize unsupported")
async def entity_not_added_if_no_air_conditioner_programs() -> None:
    """Stub for test_entity_not_added_if_no_air_conditioner_programs."""

@test.skip("indirect parametrize unsupported")
async def turn_on_off() -> None:
    """Stub for test_turn_on_off."""

@test.skip("indirect parametrize unsupported")
async def turn_on_off_exception() -> None:
    """Stub for test_turn_on_off_exception."""

@test.skip("indirect parametrize unsupported")
async def hvac_modes_programs_mapping_and_functionality() -> None:
    """Stub for test_hvac_modes_programs_mapping_and_functionality."""

@test.skip("indirect parametrize unsupported")
async def set_hvac_mode_raises_home_assistant_error_on_api_errors() -> None:
    """Stub for test_set_hvac_mode_raises_home_assistant_error_on_api_errors."""

@test.skip("indirect parametrize unsupported")
async def hvac_mode_off_functionality() -> None:
    """Stub for test_hvac_mode_off_functionality."""

@test.skip("indirect parametrize unsupported")
async def hvac_mode_off_exception() -> None:
    """Stub for test_hvac_mode_off_exception."""

@test.skip("indirect parametrize unsupported")
async def state_when_appliance_is_in_standby() -> None:
    """Stub for test_state_when_appliance_is_in_standby."""

@test.skip("indirect parametrize unsupported")
async def not_supported_functionality_if_not_power_setting() -> None:
    """Stub for test_not_supported_functionality_if_not_power_setting."""

@test.skip("indirect parametrize unsupported")
async def preset_modes_programs_mapping_and_functionality() -> None:
    """Stub for test_preset_modes_programs_mapping_and_functionality."""

@test.skip("indirect parametrize unsupported")
async def set_preset_mode_raises_home_assistant_error_on_api_errors() -> None:
    """Stub for test_set_preset_mode_raises_home_assistant_error_on_api_errors."""

@test.skip("indirect parametrize unsupported")
async def fan_mode_functionality() -> None:
    """Stub for test_fan_mode_functionality."""

@test.skip("indirect parametrize unsupported")
async def set_fan_mode_raises_home_assistant_error_on_api_errors() -> None:
    """Stub for test_set_fan_mode_raises_home_assistant_error_on_api_errors."""

@test.skip("indirect parametrize unsupported")
async def fan_mode_feature_supported() -> None:
    """Stub for test_fan_mode_feature_supported."""

@test.skip("indirect parametrize unsupported")
async def preset_mode_feature_not_supported_on_missing_active_clean() -> None:
    """Stub for test_preset_mode_feature_not_supported_on_missing_active_clean."""
