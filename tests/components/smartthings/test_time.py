"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("snapshot test - port deferred")
async def state_update() -> None:
    """Stub for test_state_update (port deferred)."""

@test.skip("snapshot test - port deferred")
async def set_value() -> None:
    """Stub for test_set_value (port deferred)."""

@test.skip("snapshot test - port deferred")
async def dnd_mode_updates() -> None:
    """Stub for test_dnd_mode_updates (port deferred)."""
