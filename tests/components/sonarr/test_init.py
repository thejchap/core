"""Tests for the Sonsrr integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_reauth() -> None:
    """Stub for test_config_entry_reauth (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_config_entry() -> None:
    """Stub for test_migrate_config_entry (port deferred)."""
