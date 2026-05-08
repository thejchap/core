"""Test for the switchbot_cloud lock. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock() -> None:
    """Stub for test_lock (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_open() -> None:
    """Stub for test_lock_open (port deferred)."""
