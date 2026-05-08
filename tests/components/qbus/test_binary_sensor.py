"""Test Qbus binary sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor (port deferred)."""
