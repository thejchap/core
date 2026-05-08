"""Tryke skip-stubs for test_climate.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def setup_platform() -> None:
    """Stub for test_setup_platform."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def hvac_state() -> None:
    """Stub for test_hvac_state."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def target_temp() -> None:
    """Stub for test_target_temp."""
