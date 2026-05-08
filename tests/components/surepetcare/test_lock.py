"""The tests for the Sure Petcare lock platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def locks() -> None:
    """Stub for test_locks (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_failing() -> None:
    """Stub for test_lock_failing (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unlock_failing() -> None:
    """Stub for test_unlock_failing (port deferred)."""
