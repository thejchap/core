"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_get_config_entry_diagnostics() -> None:
    """Stub for test_async_get_config_entry_diagnostics."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_get_device_diagnostics() -> None:
    """Stub for test_async_get_device_diagnostics."""
