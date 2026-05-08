"""Tests for the Stookwijzer services. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def service_get_forecast() -> None:
    """Stub for test_service_get_forecast (port deferred)."""

@test.skip("syrupy snapshot")
async def service_entry_not_loaded() -> None:
    """Stub for test_service_entry_not_loaded (port deferred)."""

@test.skip("syrupy snapshot")
async def service_integration_not_found() -> None:
    """Stub for test_service_integration_not_found (port deferred)."""
