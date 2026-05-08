"""Test Snoo Switches. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch() -> None:
    """Stub for test_switch (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_success() -> None:
    """Stub for test_update_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_failed() -> None:
    """Stub for test_update_failed (port deferred)."""
