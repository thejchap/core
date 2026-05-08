"""Test Statistics component setup process. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_removed() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_removed_shared_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed_shared_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_removed_from_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed_from_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_moved_other_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_moved_other_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_new_entity_id() -> None:
    """Stub for test_async_handle_source_entity_new_entity_id (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_1_1() -> None:
    """Stub for test_migration_1_1 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_from_future_version() -> None:
    """Stub for test_migration_from_future_version (port deferred)."""
