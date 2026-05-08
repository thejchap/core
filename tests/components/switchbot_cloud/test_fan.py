"""Test for the Switchbot (Battery) Circulator Fan. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def coordinator_data_is_none() -> None:
    """Stub for test_coordinator_data_is_none (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_on() -> None:
    """Stub for test_turn_on (port deferred)."""

@test.skip("syrupy snapshot")
async def turn_off() -> None:
    """Stub for test_turn_off (port deferred)."""

@test.skip("syrupy snapshot")
async def set_percentage() -> None:
    """Stub for test_set_percentage (port deferred)."""

@test.skip("syrupy snapshot")
async def set_preset_mode() -> None:
    """Stub for test_set_preset_mode (port deferred)."""

@test.skip("syrupy snapshot")
async def air_purifier() -> None:
    """Stub for test_air_purifier (port deferred)."""

@test.skip("syrupy snapshot")
async def air_purifier_controller() -> None:
    """Stub for test_air_purifier_controller (port deferred)."""
