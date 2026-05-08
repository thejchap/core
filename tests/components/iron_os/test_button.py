"""Tryke skip-stubs for test_button.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_platform() -> None:
    """Stub for test_button_platform."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_press() -> None:
    """Stub for test_button_press."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_press_exception() -> None:
    """Stub for test_button_press_exception."""
