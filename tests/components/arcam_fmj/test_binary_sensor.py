"""Tryke skip stub for test_binary_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def binary_sensor_none() -> None:
    """Stub for test_binary_sensor_none."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def binary_sensor_interlaced() -> None:
    """Stub for test_binary_sensor_interlaced."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def binary_sensor_not_interlaced() -> None:
    """Stub for test_binary_sensor_not_interlaced."""


