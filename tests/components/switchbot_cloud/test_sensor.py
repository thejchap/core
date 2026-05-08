"""Test for the switchbot_cloud sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def meter() -> None:
    """Stub for test_meter (port deferred)."""

@test.skip("syrupy snapshot")
async def plug_mini_eu() -> None:
    """Stub for test_plug_mini_eu (port deferred)."""

@test.skip("syrupy snapshot")
async def no_coordinator_data() -> None:
    """Stub for test_no_coordinator_data (port deferred)."""

@test.skip("syrupy snapshot")
async def unsupported_device_type() -> None:
    """Stub for test_unsupported_device_type (port deferred)."""
