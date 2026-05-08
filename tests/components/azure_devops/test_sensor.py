"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors_missing_data() -> None:
    """Stub for test_sensors_missing_data."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors_missing_project_definition() -> None:
    """Stub for test_sensors_missing_project_definition."""


