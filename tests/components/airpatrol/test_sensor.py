"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_with_climate_data() -> None:
    """Stub for test_sensor_with_climate_data."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_with_no_climate_data() -> None:
    """Stub for test_sensor_with_no_climate_data."""


