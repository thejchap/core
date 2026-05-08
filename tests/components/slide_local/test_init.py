"""Tests for the Slide Local integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def device_info() -> None:
    """Stub for test_device_info (port deferred)."""

@test.skip("syrupy snapshot")
async def raise_config_entry_not_ready_when_offline() -> None:
    """Stub for test_raise_config_entry_not_ready_when_offline (port deferred)."""

@test.skip("syrupy snapshot")
async def raise_config_entry_not_ready_when_empty_data() -> None:
    """Stub for test_raise_config_entry_not_ready_when_empty_data (port deferred)."""
