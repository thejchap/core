"""Tests for the Rainforest RAVEn component initialisation. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def synchronize_error() -> None:
    """Stub for test_synchronize_error (port deferred)."""

@test.skip("syrupy snapshot")
async def get_network_info_error() -> None:
    """Stub for test_get_network_info_error (port deferred)."""
