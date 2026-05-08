"""Tests for the Smart Meter B-Route sensor. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def route_b_smart_meter_sensor_update() -> None:
    """Stub for test_route_b_smart_meter_sensor_update (port deferred)."""

@test.skip("syrupy snapshot")
async def route_b_smart_meter_sensor_no_update() -> None:
    """Stub for test_route_b_smart_meter_sensor_no_update (port deferred)."""
