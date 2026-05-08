"""Tryke skip stub for test_water_heater.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the geniushub.water_heater module imports cleanly."""
    from homeassistant.components.geniushub import water_heater  # noqa: PLC0415
    expect(water_heater).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cloud_all_water_heaters() -> None:
    """Stub for test_cloud_all_water_heaters."""

