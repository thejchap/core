"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_drive.sensor module imports cleanly."""
    from homeassistant.components.google_drive import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_unknown_when_unlimited_plan() -> None:
    """Stub for test_sensor_unknown_when_unlimited_plan."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_availability() -> None:
    """Stub for test_sensor_availability."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def calculate_backups_size() -> None:
    """Stub for test_calculate_backups_size."""

