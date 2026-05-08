"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the history_stats integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.history_stats.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("history_stats")


@test.skip("recorder_mock fixture coupling")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

@test.skip("recorder_mock fixture coupling")
async def async_handle_source_entity_changes_source_entity_removed() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed."""

@test.skip("recorder_mock fixture coupling")
async def async_handle_source_entity_changes_source_entity_removed_shared_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed_shared_device."""

@test.skip("recorder_mock fixture coupling")
async def async_handle_source_entity_changes_source_entity_removed_from_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed_from_device."""

@test.skip("recorder_mock fixture coupling")
async def async_handle_source_entity_changes_source_entity_moved_other_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_moved_other_device."""

@test.skip("recorder_mock fixture coupling")
async def async_handle_source_entity_new_entity_id() -> None:
    """Stub for test_async_handle_source_entity_new_entity_id."""

@test.skip("recorder_mock fixture coupling")
async def migration_1_1() -> None:
    """Stub for test_migration_1_1."""

@test.skip("recorder_mock fixture coupling")
async def migration_1_2() -> None:
    """Stub for test_migration_1_2."""

@test.skip("recorder_mock fixture coupling")
async def migration_from_future_version() -> None:
    """Stub for test_migration_from_future_version."""
