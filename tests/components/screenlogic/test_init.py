"""Tests for ScreenLogic integration init. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_migrate_entries() -> None:
    """Stub for test_async_migrate_entries (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_migration_data() -> None:
    """Stub for test_entity_migration_data (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def platform_setup() -> None:
    """Stub for test_platform_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def retry_on_connect_exception() -> None:
    """Stub for test_retry_on_connect_exception (port deferred)."""
