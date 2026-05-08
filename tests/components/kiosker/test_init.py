"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_setup_entry_failure() -> None:
    """Stub for test_async_setup_entry_failure."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device_info() -> None:
    """Stub for test_device_info."""
