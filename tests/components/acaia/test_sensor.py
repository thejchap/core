"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def restore_state() -> None:
    """Stub for test_restore_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def battery_available_within_session_after_disconnect() -> None:
    """Stub for test_battery_available_within_session_after_disconnect."""

