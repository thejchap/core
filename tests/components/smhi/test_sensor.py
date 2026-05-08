"""Test for the smhi weather entity. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensor_setup() -> None:
    """Stub for test_sensor_setup (port deferred)."""
