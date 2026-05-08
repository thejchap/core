"""Tests for Prana integration entry points (async_setup_entry / async_unload_entry). (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def async_setup_entry_and_unload_entry() -> None:
    """Stub for test_async_setup_entry_and_unload_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def device_info_registered() -> None:
    """Stub for test_device_info_registered (port deferred)."""
