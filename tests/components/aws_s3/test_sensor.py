"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_availability() -> None:
    """Stub for test_sensor_availability."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def calculate_backups_size() -> None:
    """Stub for test_calculate_backups_size."""


