"""Tryke skip stub for test_climate.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.airpatrol.climate module imports cleanly."""
    from homeassistant.components.airpatrol import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_entities() -> None:
    """Stub for test_climate_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_entity_unavailable() -> None:
    """Stub for test_climate_entity_unavailable."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_temperature() -> None:
    """Stub for test_climate_set_temperature."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_hvac_mode() -> None:
    """Stub for test_climate_set_hvac_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_fan_mode() -> None:
    """Stub for test_climate_set_fan_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_swing_mode() -> None:
    """Stub for test_climate_set_swing_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_turn_on() -> None:
    """Stub for test_climate_turn_on."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_turn_off() -> None:
    """Stub for test_climate_turn_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_heat_mode() -> None:
    """Stub for test_climate_heat_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_temperature_api_error() -> None:
    """Stub for test_climate_set_temperature_api_error."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_fan_mode_invalid() -> None:
    """Stub for test_climate_fan_mode_invalid."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_swing_mode_invalid() -> None:
    """Stub for test_climate_swing_mode_invalid."""


