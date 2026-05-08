"""Tryke skip stub for test_binary_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def no_binary_sensor() -> None:
    """Stub for test_no_binary_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def statflag() -> None:
    """Stub for test_statflag."""


