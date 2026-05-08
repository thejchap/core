"""Test Saunum Leil integration setup and teardown. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup_and_unload() -> None:
    """Stub for test_setup_and_unload (port deferred)."""

@test.skip("syrupy snapshot")
async def async_setup_entry_connection_failed() -> None:
    """Stub for test_async_setup_entry_connection_failed (port deferred)."""

@test.skip("syrupy snapshot")
async def device_entry() -> None:
    """Stub for test_device_entry (port deferred)."""
