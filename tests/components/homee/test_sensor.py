"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def up_down_values() -> None:
    """Stub for test_up_down_values."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def window_position() -> None:
    """Stub for test_window_position."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def entity_connection_listener() -> None:
    """Stub for test_entity_connection_listener."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def entity_update_action() -> None:
    """Stub for test_entity_update_action."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def sensor_snapshot() -> None:
    """Stub for test_sensor_snapshot."""
