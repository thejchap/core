"""Tests for the SMLIGHT binary sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_binary_sensors() -> None:
    """Stub for test_all_binary_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def disabled_by_default_sensors() -> None:
    """Stub for test_disabled_by_default_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def internet_sensor_event() -> None:
    """Stub for test_internet_sensor_event (port deferred)."""
