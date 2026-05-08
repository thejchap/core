"""Tests for the sensors provided by the RDW integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def vehicle_sensors() -> None:
    """Stub for test_vehicle_sensors (port deferred)."""
