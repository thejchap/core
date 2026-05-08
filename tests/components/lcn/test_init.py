"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_setup_multiple_entries() -> None:
    """Stub for test_async_setup_multiple_entries."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_setup_entry_update() -> None:
    """Stub for test_async_setup_entry_update."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_setup_entry_fails() -> None:
    """Stub for test_async_setup_entry_fails."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_entry_reload_on_host_event_received() -> None:
    """Stub for test_async_entry_reload_on_host_event_received."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def migrate_1_1() -> None:
    """Stub for test_migrate_1_1."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def migrate_1_2() -> None:
    """Stub for test_migrate_1_2."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def migrate_2_1() -> None:
    """Stub for test_migrate_2_1."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entity_migration_on_2_1() -> None:
    """Stub for test_entity_migration_on_2_1."""
