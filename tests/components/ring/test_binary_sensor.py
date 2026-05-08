"""The tests for the Ring binary sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_not_exists_with_deprecation() -> None:
    """Stub for test_binary_sensor_not_exists_with_deprecation (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_exists_with_deprecation() -> None:
    """Stub for test_binary_sensor_exists_with_deprecation (port deferred)."""
