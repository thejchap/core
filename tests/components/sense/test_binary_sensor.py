"""The tests for Sense binary sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def on_off_sensors() -> None:
    """Stub for test_on_off_sensors (port deferred)."""
