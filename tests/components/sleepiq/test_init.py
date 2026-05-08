"""Tests for the SleepIQ integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def entry_setup_login_error() -> None:
    """Stub for test_entry_setup_login_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def entry_setup_timeout_error() -> None:
    """Stub for test_entry_setup_timeout_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_interval() -> None:
    """Stub for test_update_interval (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def api_error() -> None:
    """Stub for test_api_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def api_timeout() -> None:
    """Stub for test_api_timeout (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unique_id_migration() -> None:
    """Stub for test_unique_id_migration (port deferred)."""
