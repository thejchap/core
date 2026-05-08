"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def loading_and_unloading_config_entry() -> None:
    """Stub for test_loading_and_unloading_config_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def setup_entry_auth_error() -> None:
    """Stub for test_setup_entry_auth_error."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def setup_entry_connection_error() -> None:
    """Stub for test_setup_entry_connection_error."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device_entry() -> None:
    """Stub for test_device_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def coordinator_update_auth_error() -> None:
    """Stub for test_coordinator_update_auth_error."""
