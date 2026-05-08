"""Test pushbullet integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry_success() -> None:
    """Stub for test_async_setup_entry_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unique_id_updated() -> None:
    """Stub for test_unique_id_updated (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry_failed_invalid_api_key() -> None:
    """Stub for test_async_setup_entry_failed_invalid_api_key (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry_failed_conn_error() -> None:
    """Stub for test_async_setup_entry_failed_conn_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry_failed_json_error() -> None:
    """Stub for test_async_setup_entry_failed_json_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry_failed_urrlib3_error() -> None:
    """Stub for test_async_setup_entry_failed_urrlib3_error (port deferred)."""
