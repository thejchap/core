"""Test the initialization. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_error() -> None:
    """Stub for test_setup_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def auth_error_during_first_refresh() -> None:
    """Stub for test_auth_error_during_first_refresh (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def other_exceptions_during_first_refresh() -> None:
    """Stub for test_other_exceptions_during_first_refresh (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_config_entry() -> None:
    """Stub for test_migrate_config_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def timeout_increase_refresh() -> None:
    """Stub for test_timeout_increase_refresh (port deferred)."""
