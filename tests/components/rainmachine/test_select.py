"""Test RainMachine select entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def select_entities() -> None:
    """Stub for test_select_entities (port deferred)."""
