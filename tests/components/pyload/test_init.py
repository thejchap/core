"""Test pyLoad init. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entry_setup_unload() -> None:
    """Stub for test_entry_setup_unload (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_setup_errors() -> None:
    """Stub for test_config_entry_setup_errors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_setup_invalid_auth() -> None:
    """Stub for test_config_entry_setup_invalid_auth (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_update_invalid_auth() -> None:
    """Stub for test_coordinator_update_invalid_auth (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_setup_invalid_auth() -> None:
    """Stub for test_coordinator_setup_invalid_auth (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_update_errors() -> None:
    """Stub for test_coordinator_update_errors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration() -> None:
    """Stub for test_migration (port deferred)."""
