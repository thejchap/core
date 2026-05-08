"""Tests for the pyLoad Switches. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def state() -> None:
    """Stub for test_state (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_on_off() -> None:
    """Stub for test_turn_on_off (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_on_off_errors() -> None:
    """Stub for test_turn_on_off_errors (port deferred)."""
