"""Test init of senz integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_config_entry() -> None:
    """Stub for test_migrate_config_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_errors() -> None:
    """Stub for test_setup_errors (port deferred)."""
