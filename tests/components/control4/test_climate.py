"""Tryke skip stub for test_climate.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.control4.climate module imports cleanly."""
    from homeassistant.components.control4 import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_entities() -> None:
    """Stub for test_climate_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def hvac_action_mapping() -> None:
    """Stub for test_hvac_action_mapping."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_states() -> None:
    """Stub for test_climate_states."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_temperature() -> None:
    """Stub for test_set_temperature."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_temperature_range_auto_mode() -> None:
    """Stub for test_set_temperature_range_auto_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_not_created_when_no_initial_data() -> None:
    """Stub for test_climate_not_created_when_no_initial_data."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_missing_variables() -> None:
    """Stub for test_climate_missing_variables."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_unknown_hvac_mode() -> None:
    """Stub for test_climate_unknown_hvac_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_unknown_hvac_state() -> None:
    """Stub for test_climate_unknown_hvac_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_fan_mode() -> None:
    """Stub for test_set_fan_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def fan_mode_not_supported() -> None:
    """Stub for test_fan_mode_not_supported."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_temperature_calls_correct_api() -> None:
    """Stub for test_set_temperature_calls_correct_api."""


