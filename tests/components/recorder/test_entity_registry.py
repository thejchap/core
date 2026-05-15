"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def rename_entity_without_collision() -> None:
    """Stub for test_rename_entity_without_collision (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def rename_entity_on_mocked_platform() -> None:
    """Stub for test_rename_entity_on_mocked_platform (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def rename_entity_collision() -> None:
    """Stub for test_rename_entity_collision (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def rename_entity_collision_without_states_meta_safeguard() -> None:
    """Stub for test_rename_entity_collision_without_states_meta_safeguard (port deferred)."""
