"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def scenes() -> None:
    """Stub for test_scenes (port deferred)."""

@test.skip("snapshot test - port deferred")
async def only_new_scenes_are_created() -> None:
    """Stub for test_only_new_scenes_are_created (port deferred)."""
