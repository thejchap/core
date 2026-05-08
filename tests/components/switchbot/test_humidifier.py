"""Test the switchbot humidifiers. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def humidifier_services() -> None:
    """Stub for test_humidifier_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_humidifier_service() -> None:
    """Stub for test_exception_handling_humidifier_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def evaporative_humidifier_services() -> None:
    """Stub for test_evaporative_humidifier_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def evaporative_humidifier_services_with_exception() -> None:
    """Stub for test_evaporative_humidifier_services_with_exception (port deferred)."""
