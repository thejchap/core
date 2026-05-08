"""Tests for init platform of Remote Calendar. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def raise_for_status() -> None:
    """Stub for test_raise_for_status (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_failed() -> None:
    """Stub for test_update_failed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def calendar_parse_error() -> None:
    """Stub for test_calendar_parse_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_with_auth() -> None:
    """Stub for test_load_with_auth (port deferred)."""
