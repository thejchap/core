"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the geniushub.sensor module imports cleanly."""
    from homeassistant.components.geniushub import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cloud_all_sensors() -> None:
    """Stub for test_cloud_all_sensors."""

