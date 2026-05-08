"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""


