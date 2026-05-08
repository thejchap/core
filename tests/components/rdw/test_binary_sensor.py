"""Tests for the sensors provided by the RDW integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("translation_key entity ids differ — needs translation_helper load")
async def vehicle_binary_sensors() -> None:
    """Stub for test_vehicle_binary_sensors (port deferred)."""
