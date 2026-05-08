"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def unique_id_migration() -> None:
    """Stub for test_unique_id_migration."""


