"""Tests for the Rainforest RAVEn sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def device_update_error() -> None:
    """Stub for test_device_update_error (port deferred)."""

@test.skip("syrupy snapshot")
async def device_update_timeout() -> None:
    """Stub for test_device_update_timeout (port deferred)."""

@test.skip("syrupy snapshot")
async def device_cache() -> None:
    """Stub for test_device_cache (port deferred)."""
