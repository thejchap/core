"""Test pushbullet integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry_success() -> None:
    """Stub for test_async_setup_entry_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_failed_invalid_key() -> None:
    """Stub for test_setup_entry_failed_invalid_key (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_failed_conn_error() -> None:
    """Stub for test_setup_entry_failed_conn_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_unload_entry() -> None:
    """Stub for test_async_unload_entry (port deferred)."""
