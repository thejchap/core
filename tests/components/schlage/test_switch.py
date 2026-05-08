"""Test schlage switch. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def beeper_services() -> None:
    """Stub for test_beeper_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_and_leave_services() -> None:
    """Stub for test_lock_and_leave_services (port deferred)."""
