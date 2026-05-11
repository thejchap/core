"""Tryke skip stub for test_climate.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.balboa.climate module imports cleanly."""
    from homeassistant.components.balboa import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def climate() -> None:
    """Stub for test_climate."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_defaults_fake_tscale() -> None:
    """Stub for test_spa_defaults_fake_tscale."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_temperature() -> None:
    """Stub for test_spa_temperature."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_temperature_unit() -> None:
    """Stub for test_spa_temperature_unit."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_hvac_modes() -> None:
    """Stub for test_spa_hvac_modes."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_hvac_action() -> None:
    """Stub for test_spa_hvac_action."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_preset_modes() -> None:
    """Stub for test_spa_preset_modes."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def spa_with_blower() -> None:
    """Stub for test_spa_with_blower."""


