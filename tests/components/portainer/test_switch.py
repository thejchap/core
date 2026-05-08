"""Tests for the Portainer switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_switch_entities_snapshot() -> None:
    """Stub for test_all_switch_entities_snapshot (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_off_on() -> None:
    """Stub for test_turn_off_on (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_off_on_exceptions() -> None:
    """Stub for test_turn_off_on_exceptions (port deferred)."""
