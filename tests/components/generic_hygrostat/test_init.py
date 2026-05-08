"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the generic_hygrostat integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.generic_hygrostat import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("generic_hygrostat")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_removed() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_removed_shared_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed_shared_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_removed_from_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_removed_from_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_changes_source_entity_moved_other_device() -> None:
    """Stub for test_async_handle_source_entity_changes_source_entity_moved_other_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_handle_source_entity_new_entity_id() -> None:
    """Stub for test_async_handle_source_entity_new_entity_id."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_1_1() -> None:
    """Stub for test_migration_1_1."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_future_version() -> None:
    """Stub for test_migration_from_future_version."""

