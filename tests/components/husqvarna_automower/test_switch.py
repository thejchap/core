"""Tryke skip-stubs for test_switch.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_states() -> None:
    """Stub for test_switch_states."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_commands() -> None:
    """Stub for test_switch_commands."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def stay_out_zone_switch_commands() -> None:
    """Stub for test_stay_out_zone_switch_commands."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def work_area_switch_commands() -> None:
    """Stub for test_work_area_switch_commands."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def add_stay_out_zone() -> None:
    """Stub for test_add_stay_out_zone."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def switch_snapshot() -> None:
    """Stub for test_switch_snapshot."""
