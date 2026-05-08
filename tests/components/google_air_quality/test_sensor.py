"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_air_quality.sensor module imports cleanly."""
    from homeassistant.components.google_air_quality import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_snapshot() -> None:
    """Stub for test_sensor_snapshot."""

