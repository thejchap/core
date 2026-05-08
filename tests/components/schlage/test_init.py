"""Tests for the Schlage integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def auth_failed() -> None:
    """Stub for test_auth_failed (port deferred)."""

@test.skip("syrupy snapshot")
async def update_data_fails() -> None:
    """Stub for test_update_data_fails (port deferred)."""

@test.skip("syrupy snapshot")
async def update_data_auth_error() -> None:
    """Stub for test_update_data_auth_error (port deferred)."""

@test.skip("syrupy snapshot")
async def update_data_get_logs_auth_error() -> None:
    """Stub for test_update_data_get_logs_auth_error (port deferred)."""

@test.skip("syrupy snapshot")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def lock_device_registry() -> None:
    """Stub for test_lock_device_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def auto_add_device() -> None:
    """Stub for test_auto_add_device (port deferred)."""

@test.skip("syrupy snapshot")
async def auto_remove_device() -> None:
    """Stub for test_auto_remove_device (port deferred)."""
