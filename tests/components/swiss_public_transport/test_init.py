"""Test the swiss_public_transport integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_from() -> None:
    """Stub for test_migration_from (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_error_from_future() -> None:
    """Stub for test_migrate_error_from_future (port deferred)."""
