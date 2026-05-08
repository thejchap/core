"""Test for the switchbot_cloud binary sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def unsupported_device_type() -> None:
    """Stub for test_unsupported_device_type (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors (port deferred)."""
