"""Test the switchbot locks. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_services() -> None:
    """Stub for test_lock_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_services_with_night_latch_enabled() -> None:
    """Stub for test_lock_services_with_night_latch_enabled (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def exception_handling_lock_service() -> None:
    """Stub for test_exception_handling_lock_service (port deferred)."""
