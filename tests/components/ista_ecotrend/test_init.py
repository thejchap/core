"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def entry_setup_unload() -> None:
    """Stub for test_entry_setup_unload."""

@test.skip("snapshot test — out of scope")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""

@test.skip("snapshot test — out of scope")
async def config_entry_auth_failed() -> None:
    """Stub for test_config_entry_auth_failed."""

@test.skip("snapshot test — out of scope")
async def device_registry() -> None:
    """Stub for test_device_registry."""

@test.skip("snapshot test — out of scope")
async def update_failed() -> None:
    """Stub for test_update_failed."""

@test.skip("snapshot test — out of scope")
async def auth_failed() -> None:
    """Stub for test_auth_failed."""
