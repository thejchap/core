"""Tryke skip-stubs for mysensors test_init (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def load_unload() -> None:
    """Stub for test_load_unload (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def remove_config_entry_device() -> None:
    """Stub for test_remove_config_entry_device (port deferred)."""


