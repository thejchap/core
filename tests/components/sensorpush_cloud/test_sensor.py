"""Test SensorPush Cloud sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""
