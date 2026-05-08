"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_setup() -> None:
    """Stub for test_sensor_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_plc_phyrates() -> None:
    """Stub for test_update_plc_phyrates."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_last_update_auth_failed() -> None:
    """Stub for test_update_last_update_auth_failed."""


