"""Tests for the Rituals Perfume Genie integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_v1_to_v2() -> None:
    """Stub for test_migration_v1_to_v2 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_unload() -> None:
    """Stub for test_config_entry_unload (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_id_migration() -> None:
    """Stub for test_entity_id_migration (port deferred)."""
