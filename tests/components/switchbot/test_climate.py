"""Tests for the Switchbot climate integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def smart_thermostat_radiator_controlling() -> None:
    """Stub for test_smart_thermostat_radiator_controlling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_smart_thermostat_radiator_service() -> None:
    """Stub for test_exception_handling_smart_thermostat_radiator_service (port deferred)."""
