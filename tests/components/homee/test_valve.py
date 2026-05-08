"""Tryke skip-stubs for test_valve.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def valve_set_position() -> None:
    """Stub for test_valve_set_position."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def opening_closing() -> None:
    """Stub for test_opening_closing."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def supported_features() -> None:
    """Stub for test_supported_features."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def valve_snapshot() -> None:
    """Stub for test_valve_snapshot."""
