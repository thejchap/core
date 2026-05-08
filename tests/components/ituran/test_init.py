"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device() -> None:
    """Stub for test_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def remove_stale_devices() -> None:
    """Stub for test_remove_stale_devices."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def recover_from_errors() -> None:
    """Stub for test_recover_from_errors."""
