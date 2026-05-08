"""Test SMHI component setup process. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_and_unload_config_entry() -> None:
    """Stub for test_load_and_unload_config_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_from_future_version() -> None:
    """Stub for test_migrate_from_future_version (port deferred)."""
