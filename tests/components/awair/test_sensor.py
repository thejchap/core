"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.awair.sensor module imports cleanly."""
    from homeassistant.components.awair import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_gen1_sensors() -> None:
    """Stub for test_awair_gen1_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_gen2_sensors() -> None:
    """Stub for test_awair_gen2_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def local_awair_sensors() -> None:
    """Stub for test_local_awair_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_mint_sensors() -> None:
    """Stub for test_awair_mint_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_glow_sensors() -> None:
    """Stub for test_awair_glow_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_omni_sensors() -> None:
    """Stub for test_awair_omni_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_offline() -> None:
    """Stub for test_awair_offline."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def awair_unavailable() -> None:
    """Stub for test_awair_unavailable."""


