"""Test Suez_water sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensors_valid_state() -> None:
    """Stub for test_sensors_valid_state (port deferred)."""

@test.skip("syrupy snapshot")
async def sensors_failed_update() -> None:
    """Stub for test_sensors_failed_update (port deferred)."""
