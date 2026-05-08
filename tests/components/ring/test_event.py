"""The tests for the Ring event platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("syrupy snapshot")
async def event() -> None:
    """Stub for test_event (port deferred)."""
