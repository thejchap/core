"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_sensors() -> None:
    """Stub for test_all_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_failed() -> None:
    """Stub for test_update_failed."""


