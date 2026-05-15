"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def image_entity() -> None:
    """Stub for test_image_entity (port deferred)."""

@test.skip("snapshot test - port deferred")
async def image_update() -> None:
    """Stub for test_image_update (port deferred)."""

@test.skip("snapshot test - port deferred")
async def image_update_unavailable() -> None:
    """Stub for test_image_update_unavailable (port deferred)."""

@test.skip("snapshot test - port deferred")
async def migrate_to_new_unique_id() -> None:
    """Stub for test_migrate_to_new_unique_id (port deferred)."""
