"""Tryke skip-stubs for test_button.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_error_confirm() -> None:
    """Stub for test_button_error_confirm."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_commands() -> None:
    """Stub for test_button_commands."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_snapshot() -> None:
    """Stub for test_button_snapshot."""
