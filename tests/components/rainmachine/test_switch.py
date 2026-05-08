"""Test RainMachine switches. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def switches() -> None:
    """Stub for test_switches (port deferred)."""
