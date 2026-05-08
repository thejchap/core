"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def state_update() -> None:
    """Stub for test_state_update."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_unknown() -> None:
    """Stub for test_sensor_unknown."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def deprecated_sensor_issue() -> None:
    """Stub for test_deprecated_sensor_issue."""


