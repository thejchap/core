"""Tests for the Solarman sensor device. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot; indirect parametrize")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_availability() -> None:
    """Stub for test_sensor_availability (port deferred)."""
