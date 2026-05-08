"""The tests for the Ring number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entity_registry() -> None:
    """Stub for test_entity_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("syrupy snapshot")
async def volume_can_be_changed() -> None:
    """Stub for test_volume_can_be_changed (port deferred)."""
