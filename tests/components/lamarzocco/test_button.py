"""Tryke skip-stubs for test_button.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def start_backflush() -> None:
    """Stub for test_start_backflush."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def button_error() -> None:
    """Stub for test_button_error."""
