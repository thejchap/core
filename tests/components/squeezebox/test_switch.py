"""Tests for the Squeezebox alarm switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entity_registry() -> None:
    """Stub for test_entity_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_state() -> None:
    """Stub for test_switch_state (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_deleted() -> None:
    """Stub for test_switch_deleted (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_on() -> None:
    """Stub for test_turn_on (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_off() -> None:
    """Stub for test_turn_off (port deferred)."""

@test.skip("syrupy snapshot")
async def alarms_enabled_state() -> None:
    """Stub for test_alarms_enabled_state (port deferred)."""

@test.skip("syrupy snapshot")
async def alarms_enabled_turn_on() -> None:
    """Stub for test_alarms_enabled_turn_on (port deferred)."""

@test.skip("syrupy snapshot")
async def alarms_enabled_turn_off() -> None:
    """Stub for test_alarms_enabled_turn_off (port deferred)."""
