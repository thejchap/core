"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def config_entry() -> None:
    """Stub for test_config_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device() -> None:
    """Stub for test_device."""
