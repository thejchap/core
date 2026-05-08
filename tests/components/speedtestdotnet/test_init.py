"""Tests for SpeedTest integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_failed() -> None:
    """Stub for test_setup_failed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def entry_lifecycle() -> None:
    """Stub for test_entry_lifecycle (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def server_not_found() -> None:
    """Stub for test_server_not_found (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def get_best_server_error() -> None:
    """Stub for test_get_best_server_error (port deferred)."""
