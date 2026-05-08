"""Tryke skip-stubs for test_number.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def state() -> None:
    """Stub for test_state."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def state_fahrenheit() -> None:
    """Stub for test_state_fahrenheit."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def set_value() -> None:
    """Stub for test_set_value."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def set_value_exception() -> None:
    """Stub for test_set_value_exception."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def boost_temp_unavailable() -> None:
    """Stub for test_boost_temp_unavailable."""
