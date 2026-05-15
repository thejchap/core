"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def entity() -> None:
    """Stub for test_entity (port deferred)."""

@test.skip("snapshot test - port deferred")
async def turn_on_off() -> None:
    """Stub for test_turn_on_off (port deferred)."""

@test.skip("snapshot test - port deferred")
async def fan_set_preset_mode() -> None:
    """Stub for test_fan_set_preset_mode (port deferred)."""

@test.skip("snapshot test - port deferred")
async def fan_set_percentage() -> None:
    """Stub for test_fan_set_percentage (port deferred)."""

@test.skip("snapshot test - port deferred")
async def fan_set_direction() -> None:
    """Stub for test_fan_set_direction (port deferred)."""
