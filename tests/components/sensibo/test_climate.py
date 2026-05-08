"""The test for the sensibo climate platform."""

from tryke import expect, fixture, test

from homeassistant.components.sensibo.climate import _find_valid_target_temp


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def climate_find_valid_targets() -> None:
    """Test function to return temperature from valid targets."""
    valid_targets = [10, 16, 17, 18, 19, 20]

    expect(_find_valid_target_temp(7, valid_targets)).to_equal(10)
    expect(_find_valid_target_temp(10, valid_targets)).to_equal(10)
    expect(_find_valid_target_temp(11, valid_targets)).to_equal(16)
    expect(_find_valid_target_temp(15, valid_targets)).to_equal(16)
    expect(_find_valid_target_temp(16, valid_targets)).to_equal(16)
    expect(_find_valid_target_temp(18.5, valid_targets)).to_equal(19)
    expect(_find_valid_target_temp(20, valid_targets)).to_equal(20)
    expect(_find_valid_target_temp(25, valid_targets)).to_equal(20)


@test.skip("syrupy snapshot")
async def climate() -> None:
    """Stub for test_climate (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_fan() -> None:
    """Stub for test_climate_fan (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_swing() -> None:
    """Stub for test_climate_swing (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_horizontal_swing() -> None:
    """Stub for test_climate_horizontal_swing (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_temperatures() -> None:
    """Stub for test_climate_temperatures (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_temperature_is_none() -> None:
    """Stub for test_climate_temperature_is_none (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_hvac_mode() -> None:
    """Stub for test_climate_hvac_mode (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_on_off() -> None:
    """Stub for test_climate_on_off (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_service_failed() -> None:
    """Stub for test_climate_service_failed (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_assumed_state() -> None:
    """Stub for test_climate_assumed_state (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_no_fan_no_swing() -> None:
    """Stub for test_climate_no_fan_no_swing (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_set_timer() -> None:
    """Stub for test_climate_set_timer (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_pure_boost() -> None:
    """Stub for test_climate_pure_boost (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_climate_react() -> None:
    """Stub for test_climate_climate_react (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_climate_react_fahrenheit() -> None:
    """Stub for test_climate_climate_react_fahrenheit (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_full_ac_state() -> None:
    """Stub for test_climate_full_ac_state (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_fan_mode_and_swing_mode_not_supported() -> None:
    """Stub (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_get_device_capabilities() -> None:
    """Stub (port deferred)."""
