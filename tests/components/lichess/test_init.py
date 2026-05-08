"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device() -> None:
    """Stub for test_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def setup_entry_failed() -> None:
    """Stub for test_setup_entry_failed."""
