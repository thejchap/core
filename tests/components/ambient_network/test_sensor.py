"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors_with_no_data() -> None:
    """Stub for test_sensors_with_no_data."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors_disappearing() -> None:
    """Stub for test_sensors_disappearing."""


