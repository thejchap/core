"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_update_fail() -> None:
    """Stub for test_sensor_update_fail."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_reauth_triggered() -> None:
    """Stub for test_sensor_reauth_triggered."""


