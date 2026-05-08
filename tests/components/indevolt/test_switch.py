"""Tryke skip-stubs for test_switch.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch() -> None:
    """Stub for test_switch."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_turn_on() -> None:
    """Stub for test_switch_turn_on."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_turn_off() -> None:
    """Stub for test_switch_turn_off."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_set_value_error() -> None:
    """Stub for test_switch_set_value_error."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_availability() -> None:
    """Stub for test_switch_availability."""
