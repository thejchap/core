"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.sensor module imports cleanly."""
    from homeassistant.components.fully_kiosk import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_sensors() -> None:
    """Stub for test_sensors_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def url_sensor_truncating() -> None:
    """Stub for test_url_sensor_truncating."""

