"""Tryke skip stub for test_climate.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.comelit.climate module imports cleanly."""
    from homeassistant.components.comelit import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_data_update() -> None:
    """Stub for test_climate_data_update."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_temperature() -> None:
    """Stub for test_climate_set_temperature."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_set_temperature_when_off() -> None:
    """Stub for test_climate_set_temperature_when_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_hvac_mode() -> None:
    """Stub for test_climate_hvac_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_hvac_mode_when_off() -> None:
    """Stub for test_climate_hvac_mode_when_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_preset_mode() -> None:
    """Stub for test_climate_preset_mode."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_preset_mode_when_off() -> None:
    """Stub for test_climate_preset_mode_when_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate_remove_stale() -> None:
    """Stub for test_climate_remove_stale."""


