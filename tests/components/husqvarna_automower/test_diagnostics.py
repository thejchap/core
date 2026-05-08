"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics."""
