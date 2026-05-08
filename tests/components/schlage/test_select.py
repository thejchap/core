"""Test Schlage select. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def select() -> None:
    """Stub for test_select (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def auto_lock_time_translations() -> None:
    """Stub for test_auto_lock_time_translations (port deferred)."""
