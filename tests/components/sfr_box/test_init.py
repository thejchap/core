"""Test the SFR Box setup process. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup_unload_entry() -> None:
    """Stub for test_setup_unload_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_entry_exception() -> None:
    """Stub for test_setup_entry_exception (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_entry_auth_exception() -> None:
    """Stub for test_setup_entry_auth_exception (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_entry_invalid_auth() -> None:
    """Stub for test_setup_entry_invalid_auth (port deferred)."""

@test.skip("syrupy snapshot")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""
